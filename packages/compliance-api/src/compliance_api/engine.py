"""LiteLLM-backed implementation of the framework-neutral analysis engine port."""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any, get_type_hints

import litellm
from pydantic import BaseModel, ValidationError, create_model

from compliance_core.analysis_engine import (
    ANALYST_INSTRUCTIONS,
    AnalysisDefinition,
    AnalysisTrace,
    build_response,
    run_validated,
    upstream_error,
)
from compliance_core.contracts import AnalysisResponse
from compliance_core.errors import (
    AnalysisTimeout,
    ComplianceError,
    ConfigurationError,
    OutputValidationError,
    UpstreamModelError,
)
from compliance_core.knowledge import get_bundle
from compliance_core.ports import AnalysisEngine
from compliance_core.state import InMemoryStateStore
from compliance_core.tool_catalog import TOOL_CATALOG
from compliance_core.tools import ToolEnv, ToolSpec
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository
from compliance_skills import load_skill

from .config import ApiSettings
from .specs import AnalysisKey

logger = logging.getLogger(__name__)
MAX_TOOL_TURNS = 24


def _as_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if hasattr(value, "__dict__"):
        return vars(value)
    if isinstance(value, dict):
        return value
    return value


def _argument_model(spec: ToolSpec) -> type[BaseModel]:
    signature = inspect.signature(spec.fn)
    parameters = list(signature.parameters.values())
    if parameters and parameters[0].name == "env":
        parameters = parameters[1:]
    hints = get_type_hints(spec.fn)
    fields = {
        parameter.name: (
            hints.get(parameter.name, Any),
            ... if parameter.default is inspect.Parameter.empty else parameter.default,
        )
        for parameter in parameters
        if parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    return create_model(f"{spec.name.title().replace('_', '')}Arguments", **fields)


def _tool_definition(spec: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": _argument_model(spec).model_json_schema(),
        },
    }


class _LiteLlmConversation:
    """Chat history with the skill's tools; each message runs tool calls until a final answer."""

    def __init__(
        self, engine: "LiteLlmEngine", model: str, env: ToolEnv, specs: list[ToolSpec],
        trace: AnalysisTrace, system: str,
    ):
        self._engine, self._model, self._env, self._trace = engine, model, env, trace
        self._tools = [_tool_definition(spec) for spec in specs]
        self._by_name = {spec.name: spec for spec in specs}
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": system}]

    async def send(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        for _ in range(MAX_TOOL_TURNS):
            response = await self._engine._complete(self._model, self.messages, self._tools)
            usage = _as_plain(getattr(response, "usage", None)) or {}
            self._trace.add_usage(
                usage.get("prompt_tokens", usage.get("input_tokens", 0)),
                usage.get("completion_tokens", usage.get("output_tokens", 0)),
            )
            choices = getattr(response, "choices", None)
            if not choices:
                raise UpstreamModelError("The model provider returned no completion choices")
            message_out = choices[0].message
            tool_calls = getattr(message_out, "tool_calls", None) or []
            if not tool_calls:
                content = getattr(message_out, "content", None)
                content = content if isinstance(content, str) else ""
                self.messages.append({"role": "assistant", "content": content})
                return content
            calls = []
            for call in tool_calls:
                call_data = _as_plain(call)
                if not isinstance(call_data, dict):
                    call_data = call.model_dump(exclude_none=True)
                calls.append(call_data)
            self.messages.append(
                {"role": "assistant", "content": getattr(message_out, "content", None), "tool_calls": calls}
            )
            for call in calls:
                result = await self._call_tool(call["function"])
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["function"]["name"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        raise OutputValidationError(
            f"Model exceeded {MAX_TOOL_TURNS} tool-call turns", [f"analysis={self._engine.spec.key}"],
        )

    async def _call_tool(self, function: dict[str, Any]) -> Any:
        name = function["name"]
        spec = self._by_name.get(name)
        if spec is None:
            return {"error": f"Tool {name!r} is not allowed for skill {self._engine.spec.skill_name!r}"}
        try:
            raw_arguments = json.loads(function.get("arguments") or "{}")
            arguments = _argument_model(spec).model_validate(raw_arguments).model_dump(exclude_unset=True)
        except (json.JSONDecodeError, ValidationError) as exc:
            return {"error": f"Invalid arguments for {name}: {exc}"}
        self._trace.observe_call(name, arguments)
        self._trace.collect(arguments)
        result = spec.fn(self._env, **arguments) if _takes_env(spec) else spec.fn(**arguments)
        if inspect.isawaitable(result):
            result = await result
        self._trace.collect(result)
        return result


class LiteLlmEngine(AnalysisEngine):
    def __init__(
        self,
        spec: AnalysisDefinition,
        settings: ApiSettings,
        *,
        completion: Callable[..., Any] | None = None,
    ):
        self.spec = spec
        self.settings = settings
        self._completion = completion or litellm.acompletion
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def run(
        self, analysis: str, request: BaseModel, request_id: str | None = None
    ) -> AnalysisResponse[Any]:
        if analysis != self.spec.key:
            raise ValueError(f"Engine for {self.spec.key!r} cannot run {analysis!r}")
        request_id = request_id or uuid.uuid4().hex
        try:
            model = self.settings.model_name_for(self.spec.key)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc

        started = time.perf_counter()
        trace = AnalysisTrace()
        bundle = get_bundle()
        try:
            async with asyncio.timeout(self.settings.request_timeout_s):
                async with self._semaphore:
                    output, warnings = await run_validated(
                        self.spec, request, self._conversation(model, trace), bundle=bundle,
                        max_retries=self.settings.max_validation_retries, trace=trace,
                    )
        except TimeoutError as exc:
            raise AnalysisTimeout(
                f"Analysis exceeded {self.settings.request_timeout_s:g}s"
            ) from exc
        return build_response(
            self.spec, output, warnings, trace, request_id=request_id, model=model, bundle=bundle,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _conversation(self, model: str, trace: AnalysisTrace) -> _LiteLlmConversation:
        skill = load_skill(self.spec.skill_name)
        unknown = set(skill.allowed_tools) - set(TOOL_CATALOG)
        if unknown:
            raise ConfigurationError(f"Skill {skill.name!r} names unknown tools: {sorted(unknown)}")
        dh = self.settings.enable_dh
        env = ToolEnv(
            state=InMemoryStateStore(),
            bundle=get_bundle(),
            specifications=DhSpecificationRepository() if dh else None,
            entities=DhEntityCatalog() if dh else None,
        )
        specs = [
            TOOL_CATALOG[name] for name in skill.allowed_tools if dh or TOOL_CATALOG[name].group != "dh"
        ]
        system = f"{ANALYST_INSTRUCTIONS}\n{skill.instructions}"
        return _LiteLlmConversation(self, model, env, specs, trace, system)

    async def _complete(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        kwargs: dict[str, Any] = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"}
        if self.settings.llm_api_key is not None:
            kwargs["api_key"] = self.settings.llm_api_key.get_secret_value()
        if self.settings.llm_api_base:
            kwargs["api_base"] = self.settings.llm_api_base
        if self.settings.structured_temperature is not None:
            kwargs["temperature"] = self.settings.structured_temperature
        try:
            return await self._completion(**kwargs)
        except ComplianceError:
            raise
        except Exception as exc:
            logger.exception("LiteLLM request failed")
            raise upstream_error(exc) from exc


def _takes_env(spec: ToolSpec) -> bool:
    parameters = list(inspect.signature(spec.fn).parameters.values())
    return bool(parameters and parameters[0].name == "env")


class AnalysisRegistry:
    def __init__(
        self,
        settings: ApiSettings,
        *,
        completion: Callable[..., Any] | None = None,
    ):
        from .specs import ALL_SPECS

        self.bundle = get_bundle()
        self._engines = {
            spec.key: LiteLlmEngine(spec, settings, completion=completion) for spec in ALL_SPECS
        }

    def get(self, key: AnalysisKey) -> LiteLlmEngine:
        return self._engines[key]


class DelegatedAnalysisEngine:
    """`AnalysisEngine` port over the LiteLLM registry, for delegated tools in other adapters."""

    def __init__(self, registry: AnalysisRegistry):
        self.registry = registry

    async def run(
        self, analysis: str, request: BaseModel, request_id: str | None = None
    ) -> AnalysisResponse[Any]:
        return await self.registry.get(analysis).run(analysis, request, request_id)


def create_delegated_engine(settings: ApiSettings | None = None) -> DelegatedAnalysisEngine:
    """Build the LiteLLM engine, failing early when no analysis model is configured."""
    settings = settings or ApiSettings()
    try:
        for key in ("project_context", "dataset", "model"):
            settings.model_name_for(key)
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc
    return DelegatedAnalysisEngine(AnalysisRegistry(settings))


__all__ = ["AnalysisRegistry", "DelegatedAnalysisEngine", "LiteLlmEngine", "create_delegated_engine"]
