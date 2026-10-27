"""LiteLLM-backed implementation of the framework-neutral analysis engine port."""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
import time
import uuid
from collections.abc import Callable
from typing import Any, get_type_hints

import litellm
from pydantic import BaseModel, ValidationError, create_model

from compliance_core.contracts import AnalysisMeta, AnalysisResponse, TokenUsage
from compliance_core.errors import (
    AnalysisTimeout,
    ComplianceError,
    ConfigurationError,
    OutputValidationError,
    UpstreamModelError,
    UpstreamRateLimited,
)
from compliance_core.knowledge import get_bundle
from compliance_core.ports import AnalysisEngine
from compliance_core.state import InMemoryStateStore
from compliance_core.tool_catalog import TOOL_CATALOG
from compliance_core.tools import ToolEnv, ToolSpec
from compliance_core.validation_tools import (
    validate_dataset_compliance,
    validate_model_compliance,
    validate_project_context,
)
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository
from compliance_skills import load_skill

from .config import ApiSettings
from .specs import AnalysisKey, AnalysisSpec

logger = logging.getLogger(__name__)
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)

_VALIDATORS: dict[str, Callable[..., dict[str, Any]]] = {
    "project_context": validate_project_context,
    "dataset": validate_dataset_compliance,
    "model": validate_model_compliance,
}


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


def _collect_grounding(value: Any, paths: dict[str, None]) -> None:
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str) and path.endswith(".md"):
            paths[path] = None
        for item in value.values():
            _collect_grounding(item, paths)
    elif isinstance(value, list):
        for item in value:
            _collect_grounding(item, paths)


class LiteLlmEngine(AnalysisEngine):
    def __init__(
        self,
        spec: AnalysisSpec,
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
        try:
            async with asyncio.timeout(self.settings.request_timeout_s):
                async with self._semaphore:
                    output, warnings, trace = await self._run_validated(model, request)
        except TimeoutError as exc:
            raise AnalysisTimeout(
                f"Analysis exceeded {self.settings.request_timeout_s:g}s"
            ) from exc

        return AnalysisResponse[type(output.result)](
            data=output.result,
            meta=AnalysisMeta(
                request_id=request_id,
                agent=self.spec.agent_name,
                model=model,
                okf_version=get_bundle().version,
                latency_ms=int((time.perf_counter() - started) * 1000),
                attempts=trace["attempts"],
                grounding=list(trace["grounding"]),
                assumptions=output.assumptions,
                warnings=warnings,
                usage=TokenUsage(
                    input_tokens=trace["input_tokens"],
                    output_tokens=trace["output_tokens"],
                ),
            ),
        )

    async def _run_validated(self, model: str, request: BaseModel):
        skill = load_skill(self.spec.skill_name)
        env = ToolEnv(
            state=InMemoryStateStore(),
            bundle=get_bundle(),
            specifications=DhSpecificationRepository(),
            entities=DhEntityCatalog(),
        )
        specs = [TOOL_CATALOG[name] for name in skill.allowed_tools if name in TOOL_CATALOG]
        unknown = set(skill.allowed_tools) - set(TOOL_CATALOG)
        if unknown:
            raise ConfigurationError(f"Skill {skill.name!r} names unknown tools: {sorted(unknown)}")
        tools = [_tool_definition(tool) for tool in specs]
        by_name = {tool.name: tool for tool in specs}
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI compliance analyst. Follow this skill exactly. Ground facts in "
                    "the OKF tools, use only catalog ids returned by tools, and list assumptions "
                    "when using general knowledge. Return only the output JSON object.\n\n"
                    + skill.instructions
                ),
            },
            {"role": "user", "content": request.model_dump_json(exclude_none=True)},
        ]
        trace: dict[str, Any] = {
            "attempts": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "grounding": {},
        }
        max_turns = 24
        for attempt in range(1, self.settings.max_validation_retries + 2):
            trace["attempts"] = attempt
            text = await self._invoke(model, messages, tools, by_name, env, trace, max_turns)
            try:
                output = self.spec.output_model.model_validate_json(text)
            except ValidationError as exc:
                problems = [
                    f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                    for error in exc.errors()[:10]
                ]
                output, errors, warnings = None, problems, []
            else:
                result = _VALIDATORS[self.spec.key](request, output, env.bundle)
                output = (
                    self.spec.output_model.model_validate(result["normalized"])
                    if result.get("normalized")
                    else None
                )
                errors = [issue["message"] for issue in result.get("errors", [])]
                warnings = [issue["message"] for issue in result.get("warnings", [])]
            if output is not None and not errors:
                return output, warnings, trace
            messages.append(
                {
                    "role": "user",
                    "content": "Your previous answer was rejected:\n- "
                    + "\n- ".join(errors)
                    + "\nReturn the complete corrected JSON object only.",
                }
            )
        raise OutputValidationError("The model did not produce valid output", errors)

    async def _invoke(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        by_name: dict[str, ToolSpec],
        env: ToolEnv,
        trace: dict[str, Any],
        max_turns: int,
    ) -> str:
        for _ in range(max_turns):
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            }
            if self.settings.llm_api_key is not None:
                kwargs["api_key"] = self.settings.llm_api_key.get_secret_value()
            if self.settings.llm_api_base:
                kwargs["api_base"] = self.settings.llm_api_base
            if self.settings.structured_temperature is not None:
                kwargs["temperature"] = self.settings.structured_temperature

            try:
                response = await self._completion(**kwargs)
            except ComplianceError:
                raise
            except Exception as exc:
                if getattr(exc, "status_code", None) == 429 or "RateLimit" in type(exc).__name__:
                    raise UpstreamRateLimited("The model provider rate limit was reached") from exc
                logger.exception("LiteLLM request failed")
                raise UpstreamModelError(f"{type(exc).__name__}: {str(exc)[:300]}") from exc

            usage = _as_plain(getattr(response, "usage", None)) or {}
            trace["input_tokens"] += usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
            trace["output_tokens"] += usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
            choices = getattr(response, "choices", None)
            if not choices:
                raise UpstreamModelError("The model provider returned no completion choices")
            choice = choices[0]
            message = choice.message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                content = getattr(message, "content", None)
                content = content if isinstance(content, str) else ""
                if fenced := _FENCE.match(content.strip()):
                    content = fenced.group(1)
                messages.append({"role": "assistant", "content": content})
                return content

            normalized_calls = []
            for call in tool_calls:
                call_data = _as_plain(call)
                if not isinstance(call_data, dict):
                    call_data = call.model_dump(exclude_none=True)
                normalized_calls.append(call_data)
            messages.append(
                {
                    "role": "assistant",
                    "content": getattr(message, "content", None),
                    "tool_calls": normalized_calls,
                }
            )
            for call in normalized_calls:
                function = call["function"]
                name = function["name"]
                spec = by_name.get(name)
                if spec is None:
                    result = {"error": f"Tool {name!r} is not allowed for skill {self.spec.skill_name!r}"}
                else:
                    try:
                        raw_arguments = json.loads(function.get("arguments") or "{}")
                        arguments = _argument_model(spec).model_validate(raw_arguments).model_dump(
                            exclude_unset=True
                        )
                    except (json.JSONDecodeError, ValidationError) as exc:
                        result = {"error": f"Invalid arguments for {name}: {exc}"}
                    else:
                        _collect_grounding(arguments, trace["grounding"])
                        result_value = (
                            spec.fn(env, **arguments) if _takes_env(spec) else spec.fn(**arguments)
                        )
                        if inspect.isawaitable(result_value):
                            result_value = await result_value
                        _collect_grounding(result_value, trace["grounding"])
                        result = result_value
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
        raise OutputValidationError(
            f"Model exceeded {max_turns} tool-call turns",
            [f"analysis={self.spec.key}"],
        )


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


__all__ = ["AnalysisRegistry", "LiteLlmEngine"]
