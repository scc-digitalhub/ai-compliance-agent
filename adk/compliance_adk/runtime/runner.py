"""Runs a structured agent for one request: fresh session, validation with retry, response envelope."""
from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from google.adk.events import Event
from google.adk.models.base_llm import BaseLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, ValidationError

from ..agents.specs import StructuredAgentSpec
from ..agents.structured import build_structured_agent
from ..config import Settings, get_settings
from ..contracts import AnalysisMeta, AnalysisResponse, TokenUsage
from ..errors import (
    AnalysisTimeout,
    ComplianceAdkError,
    OutputValidationError,
    UpstreamModelError,
    UpstreamRateLimited,
)
from ..knowledge import OkfBundle, get_bundle
from .validation import VALIDATORS, Issue

logger = logging.getLogger(__name__)

APP_NAME = "compliance_structured"
_PATH_TOOLS = {"read_okf_concept", "list_okf_directory"}
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


@dataclass
class _Trace:
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    grounding: dict[str, None] = field(default_factory=dict)  # insertion-ordered set

    def observe(self, event: Event) -> None:
        usage = event.usage_metadata
        if usage:
            self.input_tokens += usage.prompt_token_count or 0
            self.output_tokens += usage.candidates_token_count or 0
        for call in event.get_function_calls():
            path = (call.args or {}).get("path")
            if call.name in _PATH_TOOLS and isinstance(path, str) and path:
                self.grounding[path] = None
        for response in event.get_function_responses():
            self._collect_paths(response.response)

    def _collect_paths(self, obj: Any) -> None:
        if isinstance(obj, dict):
            path = obj.get("path")
            if isinstance(path, str) and path.endswith(".md"):
                self.grounding[path] = None
            for value in obj.values():
                self._collect_paths(value)
        elif isinstance(obj, list):
            for value in obj:
                self._collect_paths(value)


def _map_upstream(exc: Exception) -> ComplianceAdkError:
    if getattr(exc, "status_code", None) == 429 or "RateLimit" in type(exc).__name__:
        return UpstreamRateLimited("The model provider rate limit was reached")
    return UpstreamModelError(f"{type(exc).__name__}: {str(exc)[:300]}")


def _schema_problems(exc: ValidationError) -> list[str]:
    return [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()[:10]]


class _Rejected(Exception):
    """The agent's answer failed ADK's own output_schema validation."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


class StructuredRunner:
    def __init__(
        self,
        spec: StructuredAgentSpec,
        settings: Settings | None = None,
        model: BaseLlm | str | None = None,
        bundle: OkfBundle | None = None,
    ):
        self.spec = spec
        self.settings = settings or get_settings()
        self.bundle = bundle or get_bundle()
        self.agent = build_structured_agent(spec, self.settings, model)
        self.model_name = getattr(self.agent.model, "model", None) or str(self.agent.model)
        self._sessions = InMemorySessionService()
        self._runner = Runner(agent=self.agent, app_name=APP_NAME, session_service=self._sessions)
        self._sem: asyncio.Semaphore | None = None
        self._sem_loop: asyncio.AbstractEventLoop | None = None

    def _semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._sem is None or self._sem_loop is not loop:  # semaphores are bound to one event loop
            self._sem, self._sem_loop = asyncio.Semaphore(self.settings.max_concurrency), loop
        return self._sem

    async def run(self, request: BaseModel, request_id: str | None = None) -> AnalysisResponse[Any]:
        request_id = request_id or uuid.uuid4().hex
        started = time.perf_counter()
        try:
            async with asyncio.timeout(self.settings.request_timeout_s):
                async with self._semaphore():
                    output, warnings, trace = await self._run_validated(request, request_id)
        except TimeoutError as exc:
            raise AnalysisTimeout(
                f"Analysis exceeded {self.settings.request_timeout_s:g}s"
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "analysis agent=%s request_id=%s attempts=%d latency_ms=%d",
            self.spec.agent_name, request_id, trace.attempts, latency_ms,
        )
        meta = AnalysisMeta(
            request_id=request_id,
            agent=self.spec.agent_name,
            model=self.model_name,
            okf_version=self.bundle.version,
            latency_ms=latency_ms,
            attempts=trace.attempts,
            grounding=list(trace.grounding),
            assumptions=output.assumptions,
            warnings=warnings,
            usage=TokenUsage(input_tokens=trace.input_tokens, output_tokens=trace.output_tokens),
        )
        return AnalysisResponse[type(output.result)](data=output.result, meta=meta)

    async def _run_validated(self, request: BaseModel, request_id: str):
        session = await self._sessions.create_session(app_name=APP_NAME, user_id=request_id)
        trace = _Trace()
        message = request.model_dump_json(exclude_none=True)
        problems: list[str] = []
        try:
            for attempt in range(1, self.settings.max_validation_retries + 2):
                trace.attempts = attempt
                try:
                    text = await self._invoke(session.id, request_id, message, trace)
                except _Rejected as rejected:
                    output, issues = None, [Issue("error", p) for p in rejected.problems]
                else:
                    output, issues = self._parse_and_validate(text, request)
                errors = [i.message for i in issues if i.severity == "error"]
                if output is not None and not errors:
                    return output, [i.message for i in issues], trace
                problems = errors
                message = (
                    "Your previous answer was rejected:\n- "
                    + "\n- ".join(problems)
                    + "\nReturn the complete corrected JSON object only."
                )
            raise OutputValidationError("The model did not produce valid output", problems)
        finally:
            await self._sessions.delete_session(app_name=APP_NAME, user_id=request_id, session_id=session.id)

    async def _invoke(self, session_id: str, user_id: str, message: str, trace: _Trace) -> str:
        content = types.Content(role="user", parts=[types.Part(text=message)])
        final_text = ""
        try:
            async for event in self._runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                trace.observe(event)
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(p.text or "" for p in event.content.parts)
        except ComplianceAdkError:
            raise
        except ValidationError as exc:
            raise _Rejected(_schema_problems(exc)) from exc
        except Exception as exc:
            raise _map_upstream(exc) from exc
        return final_text

    def _parse_and_validate(self, text: str, request: BaseModel) -> tuple[BaseModel | None, list[Issue]]:
        text = text.strip()
        if fenced := _FENCE.match(text):
            text = fenced.group(1)
        if not text:
            return None, [Issue("error", "the answer was empty")]
        try:
            output = self.spec.output_schema.model_validate_json(text)
        except ValidationError as exc:
            return None, [Issue("error", p) for p in _schema_problems(exc)]
        return output, VALIDATORS[self.spec.key](output.result, request, self.bundle)
