# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Runs a structured ADK agent for one request using the core validate-and-retry loop."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

from google.adk.models.base_llm import BaseLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, ValidationError

from ..agents.specs import StructuredAgentSpec
from ..agents.structured import build_structured_agent
from ..config import Settings, get_settings
from compliance_core.analysis_engine import (
    AnalysisTrace,
    OutputRejected,
    build_response,
    run_validated,
    schema_problems,
    upstream_error,
)
from compliance_core.contracts import AnalysisResponse
from compliance_core.errors import AnalysisTimeout, ComplianceError
from compliance_core.knowledge import OkfBundle, get_bundle

logger = logging.getLogger(__name__)

APP_NAME = "compliance_structured"


class _AdkConversation:
    """One ADK session; each message runs the agent until its final answer."""

    def __init__(self, runner: Runner, user_id: str, session_id: str, trace: AnalysisTrace):
        self._runner, self._user_id, self._session_id, self._trace = runner, user_id, session_id, trace

    async def send(self, message: str) -> str:
        content = types.Content(role="user", parts=[types.Part(text=message)])
        final_text = ""
        try:
            async for event in self._runner.run_async(
                user_id=self._user_id, session_id=self._session_id, new_message=content,
            ):
                usage = event.usage_metadata
                if usage:
                    self._trace.add_usage(usage.prompt_token_count, usage.candidates_token_count)
                for call in event.get_function_calls():
                    self._trace.observe_call(call.name, call.args or {})
                for response in event.get_function_responses():
                    self._trace.collect(response.response)
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(p.text or "" for p in event.content.parts)
        except ValidationError as exc:
            # ADK validates the answer against output_schema before returning it.
            raise OutputRejected(schema_problems(exc)) from exc
        except ComplianceError:
            raise
        except Exception as exc:
            raise upstream_error(exc) from exc
        return final_text


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
        trace = AnalysisTrace()
        try:
            async with asyncio.timeout(self.settings.request_timeout_s):
                async with self._semaphore():
                    output, warnings = await self._run_validated(request, request_id, trace)
        except TimeoutError as exc:
            raise AnalysisTimeout(
                f"Analysis exceeded {self.settings.request_timeout_s:g}s"
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "analysis agent=%s request_id=%s attempts=%d latency_ms=%d",
            self.spec.agent_name, request_id, trace.attempts, latency_ms,
        )
        return build_response(
            self.spec, output, warnings, trace, request_id=request_id, model=self.model_name,
            bundle=self.bundle, latency_ms=latency_ms,
        )

    async def _run_validated(self, request: BaseModel, request_id: str, trace: AnalysisTrace):
        session = await self._sessions.create_session(app_name=APP_NAME, user_id=request_id)
        try:
            return await run_validated(
                self.spec, request, _AdkConversation(self._runner, request_id, session.id, trace),
                bundle=self.bundle, max_retries=self.settings.max_validation_retries, trace=trace,
            )
        finally:
            await self._sessions.delete_session(app_name=APP_NAME, user_id=request_id, session_id=session.id)
