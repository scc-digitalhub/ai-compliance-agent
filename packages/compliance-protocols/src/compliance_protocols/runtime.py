"""Durable, transport-neutral conversation runner with project and write boundaries."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from collections.abc import MutableMapping
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

from google.adk.agents import LlmAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.agents.tool_adapter import AdkAnalysisEngine, TOOL_ENV_FACTORY
from compliance_core.knowledge import get_bundle
from compliance_core.ports import EntityKind, SpecificationKind
from compliance_core.specification_tools import (
    _SPECIFICATIONS, _session_specification, _validate, save_compliance_specification,
)
from compliance_core.state import MappingStateStore, entity_project
from compliance_core.tools import ToolEnv
from compliance_dh.repositories import DhEntityCatalog, DhSpecificationRepository

from .config import ProtocolSettings

logger = logging.getLogger(__name__)
APP = "compliance_protocols"
USER = "single_tenant"
BOUND_PROJECT = "protocol_project"
PENDING = "protocol_pending_write"
Status = Literal["completed", "input_required", "failed", "cancelled"]
Notify = Callable[[dict[str, Any]], Awaitable[None]]
Permission = Callable[[dict[str, Any]], Awaitable[bool]]

PROTOCOL_INSTRUCTION = """
Protocol interaction rules:
- Use request_user_input(question) whenever you need missing inputs, project selection, or the user's
  decision about re-running an existing analysis. Do not claim completion while awaiting input.
- DigitalHub writes are disabled unless the deployment enables them, and each write requires a
  separate transport-level approval. An approval_required tool response is not a successful save.
  Relay its approval id and exact operation; never approve a write yourself or retry to bypass it.
- A conversation is bound to the first DigitalHub project explicitly used. To switch projects,
  ask the user to start a new conversation. DigitalHub credentials determine project access;
  never select a default project from environment variables.
- Validated tool results are delivered separately as JSON; explain them without fabricating results.
"""


@dataclass
class Turn:
    notify: Notify
    permission: Permission | None = None
    status: Status = "completed"
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    authorized_write: str | None = None
    error: str | None = None
    grounding: dict[str, None] = field(default_factory=dict)


CURRENT: ContextVar[Turn] = ContextVar("compliance_protocol_turn")


@dataclass
class TurnResult:
    status: Status
    text: str
    artifacts: list[dict[str, Any]]
    approval: dict[str, Any] | None = None


def _digest(operation: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(operation, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request_user_input(question: str) -> dict[str, Any]:
    """Ask the user for required information or a decision before continuing."""
    CURRENT.get().status = "input_required"
    return {"input_required": True, "question": question}


class ProjectPolicy:
    def __init__(self, state: MappingStateStore, settings: ProtocolSettings):
        self.state, self.settings = state, settings

    def resolve(self, kind: str, entity: str, project: str | None) -> str:
        if kind == "project":
            selected = entity.strip()
        elif entity.startswith("store://"):
            selected = urlparse(entity).netloc
            if project and selected != project:
                raise PermissionError("The project argument conflicts with the store:// key")
        else:
            selected = entity_project(self.state, project)
        if not selected:
            raise ValueError("An explicit DigitalHub project is required")
        bound = self.state.get(BOUND_PROJECT)
        if bound and selected != bound:
            raise PermissionError("This conversation is bound to another project; start a new conversation")
        self.state[BOUND_PROJECT] = selected
        return selected


class ScopedSpecifications:
    def __init__(self, policy: ProjectPolicy, repository: DhSpecificationRepository):
        self.policy, self.repository = policy, repository

    def get(self, kind: SpecificationKind, entity: str, project: str | None = None) -> dict[str, Any]:
        selected = self.policy.resolve(kind, entity, project)
        return self.repository.get(kind, entity, project=selected)

    def save(
        self, kind: SpecificationKind, entity: str, specification: dict[str, Any],
        project: str | None = None,
    ) -> None:
        selected = self.policy.resolve(kind, entity, project)
        operation = {"kind": kind, "entity": entity, "project": selected, "specification": specification}
        turn = CURRENT.get()
        if not self.policy.settings.allow_writes or turn.authorized_write != _digest(operation):
            raise PermissionError("This exact write has not been approved")
        turn.authorized_write = None
        self.repository.save(kind, entity, specification, project=selected)


class ScopedEntities:
    def __init__(self, policy: ProjectPolicy, catalog: DhEntityCatalog):
        self.policy, self.catalog = policy, catalog

    def get(self, kind: EntityKind, entity: str, project: str | None = None) -> dict[str, Any]:
        selected = self.policy.resolve(kind, entity, project)
        return self.catalog.get(kind, entity, project=selected)


class ConversationRuntime:
    def __init__(
        self, settings: ProtocolSettings, *, agent: LlmAgent | None = None,
        specifications: DhSpecificationRepository | None = None,
        entities: DhEntityCatalog | None = None,
    ):
        self.settings = settings
        directory = settings.prepare_directory()
        self.sessions = DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{directory / 'sessions.db'}")
        self.specifications = specifications or DhSpecificationRepository()
        self.entities = entities or DhEntityCatalog()
        self.agent = agent or build_coordinator_agent()
        original_instruction = self.agent.instruction

        async def instructions(ctx):
            base = original_instruction(ctx) if callable(original_instruction) else original_instruction
            if isinstance(base, Awaitable):
                base = await base
            return (base or "") + PROTOCOL_INSTRUCTION

        self.agent.instruction = instructions
        self.agent.tools = [*self.agent.tools, FunctionTool(request_user_input)]
        self.agent.before_tool_callback = self.before_tool
        self.agent.after_tool_callback = self.after_tool
        self.runner = Runner(agent=self.agent, app_name=APP, session_service=self.sessions)
        self._locks: dict[str, asyncio.Lock] = {}
        self._active: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    def environment(self, ctx: ToolContext) -> ToolEnv:
        return self.environment_for_state(ctx.state)

    def environment_for_state(self, values: MutableMapping[str, Any]) -> ToolEnv:
        state = MappingStateStore(values)
        policy = ProjectPolicy(state, self.settings)
        return ToolEnv(
            state=state, bundle=get_bundle(),
            specifications=ScopedSpecifications(policy, self.specifications),
            entities=ScopedEntities(policy, self.entities), analysis_engine=AdkAnalysisEngine(),
        )

    async def create(self, cwd: str | None = None, session_id: str | None = None) -> str:
        session = await self.sessions.create_session(
            app_name=APP, user_id=USER, session_id=session_id,
            state={"protocol_cwd": cwd},
        )
        return session.id

    async def get(self, session_id: str):
        session = await self.sessions.get_session(app_name=APP, user_id=USER, session_id=session_id)
        if session is None:
            raise ValueError("Unknown conversation")
        return session

    async def history(self, session_id: str) -> list[dict[str, str]]:
        session = await self.get(session_id)
        return [
            {"role": event.content.role or "model", "text": part.text}
            for event in session.events if event.content and not event.partial
            for part in event.content.parts or [] if part.text and not part.thought
        ]

    async def before_tool(self, tool, args: dict[str, Any], tool_context: ToolContext):
        turn = CURRENT.get()
        await turn.notify({"type": "tool_start", "id": tool_context.function_call_id, "name": tool.name})
        if tool.name in ("get_entity_details", "get_compliance_specification", "save_compliance_specification"):
            try:
                ProjectPolicy(MappingStateStore(tool_context.state), self.settings).resolve(
                    args["kind"], args["entity"], args.get("project")
                )
            except (ValueError, PermissionError) as exc:
                turn.status = "input_required"
                return {"code": "project_required_or_denied", "error": str(exc)}
        if tool.name in ("analyze_project_context", "analyze_dataset", "analyze_model", "record_compliance_analysis"):
            request = args
            if tool.name == "record_compliance_analysis":
                request = args.get("request", {})
                if isinstance(request, str):
                    request = json.loads(request)
            project = request if tool.name == "record_compliance_analysis" and args.get("kind") == "project" else request.get("project")
            if project:
                if isinstance(project, str):
                    project = json.loads(project)
                try:
                    ProjectPolicy(MappingStateStore(tool_context.state), self.settings).resolve(
                        "project", project["name"], None
                    )
                except (ValueError, PermissionError) as exc:
                    turn.status = "input_required"
                    return {"code": "project_not_authorized", "error": str(exc)}
        if tool.name != "save_compliance_specification":
            return None
        if not self.settings.allow_writes:
            return {"code": "writes_disabled", "error": "DigitalHub writes are disabled by deployment policy"}
        state = tool_context.state
        if state.get(PENDING) and state[PENDING]["expires_at"] < time.time():
            state[PENDING] = None
        if state.get(PENDING):
            turn.status = "input_required"
            return {"code": "approval_required", "approval": state[PENDING]}
        try:
            kind, entity = args["kind"], args["entity"]
            selected = ProjectPolicy(MappingStateStore(state), self.settings).resolve(
                kind, entity, args.get("project")
            )
            raw = args.get("specification") or _session_specification(state, kind, entity)
            if not raw:
                return {"code": "not_found", "error": "No specification available to save"}
            normalized = _validate(_SPECIFICATIONS[kind][1], raw).model_dump(mode="json", exclude_none=True)
        except (ValueError, PermissionError, KeyError) as exc:
            turn.status = "input_required"
            return {"code": "invalid_write", "error": str(exc)}
        operation = {"kind": kind, "entity": entity, "project": selected, "specification": normalized}
        approval = {"id": uuid.uuid4().hex, "operation": operation, "expires_at": time.time() + self.settings.approval_ttl_s}
        if turn.permission is not None:
            if not await turn.permission(approval):
                return {"code": "permission_denied", "error": "The user did not approve this write"}
            if approval["expires_at"] < time.time():
                turn.status = "input_required"
                return {"code": "approval_expired", "error": "This write approval expired; request it again"}
            args.update(operation)
            turn.authorized_write = _digest(operation)
            return None
        state[PENDING] = approval
        turn.status = "input_required"
        return {"code": "approval_required", "approval": approval}

    async def after_tool(self, tool, args, tool_context, tool_response):
        turn = CURRENT.get()
        def collect_paths(value):
            if isinstance(value, dict):
                path = value.get("path")
                if isinstance(path, str) and path.endswith(".md"):
                    turn.grounding[path] = None
                for item in value.values():
                    collect_paths(item)
            elif isinstance(value, list):
                for item in value:
                    collect_paths(item)

        collect_paths(tool_response)
        if tool.name == "read_okf_concept" and isinstance(args.get("path"), str):
            turn.grounding[args["path"]] = None
        await turn.notify({
            "type": "tool_end", "id": tool_context.function_call_id,
            "name": tool.name, "result": tool_response,
        })
        if not isinstance(tool_response, dict):
            return None
        if tool_response.get("code") in ("missing_project", "approval_required") or tool_response.get("stored_on_dh"):
            turn.status = "input_required"
        if tool_response.get("input_required"):
            turn.status = "input_required"
        if "error" in tool_response and turn.status != "input_required":
            turn.status = "failed"
            turn.error = tool_response["error"]
        if tool.name.startswith("analyze_") and "data" in tool_response:
            turn.artifacts.append({"tool": tool.name, **tool_response})
        if tool.name == "record_compliance_analysis" and tool_response.get("stored"):
            turn.artifacts.append({
                "tool": tool.name, **tool_response,
                "meta": {"okf_version": get_bundle().version, "grounding": list(turn.grounding)},
            })
        if tool.name == "get_compliance_specification" and "specification" in tool_response:
            turn.artifacts.append({"tool": tool.name, **tool_response})
        return None

    async def prompt(
        self, session_id: str, text: str, notify: Notify, *,
        permission: Permission | None = None, approval_id: str | None = None,
        approve: bool | None = None,
    ) -> TurnResult:
        lock = self._locks.setdefault(session_id, asyncio.Lock())
        if lock.locked():
            raise ValueError("A turn is already running in this conversation")
        async with lock:
            session = await self.get(session_id)
            turn = Turn(notify=notify, permission=permission)
            token = CURRENT.set(turn)
            env_token = TOOL_ENV_FACTORY.set(self.environment)
            active = asyncio.current_task()
            if active is not None:
                self._active[session_id] = active
            output = []
            streamed = False
            try:
                async with asyncio.timeout(self.settings.timeout_s), self._semaphore:
                    if approval_id is not None:
                        return await self._approve(session, turn, approval_id, approve)
                    if not text.strip():
                        raise ValueError("A non-empty text prompt is required")
                    async for event in self.runner.run_async(
                        user_id=USER, session_id=session_id,
                        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
                        run_config=RunConfig(streaming_mode=StreamingMode.SSE, max_llm_calls=32),
                    ):
                        if event.error_code:
                            turn.status, turn.error = "failed", event.error_message or event.error_code
                        if event.content and event.partial:
                            for part in event.content.parts or []:
                                if part.text and not part.thought:
                                    streamed = True
                                    await notify({"type": "text", "text": part.text})
                        elif event.content and event.is_final_response():
                            for part in event.content.parts or []:
                                if part.text and not part.thought:
                                    output.append(part.text)
                                    if not streamed:
                                        await notify({"type": "text", "text": part.text})
                current = await self.get(session_id)
                return TurnResult(turn.status, turn.error or "\n".join(output), turn.artifacts, current.state.get(PENDING))
            except asyncio.CancelledError:
                return TurnResult("cancelled", "Execution cancelled; verify any write already in progress.", turn.artifacts)
            except TimeoutError:
                return TurnResult("failed", "Execution exceeded the configured time limit.", turn.artifacts)
            except Exception:
                logger.exception("Protocol turn failed for session %s", session_id)
                return TurnResult("failed", "Agent execution failed; consult the server logs.", turn.artifacts)
            finally:
                self._active.pop(session_id, None)
                TOOL_ENV_FACTORY.reset(env_token)
                CURRENT.reset(token)

    async def _approve(self, session, turn: Turn, approval_id: str, approve: bool | None) -> TurnResult:
        pending = session.state.get(PENDING)
        if not pending or pending["id"] != approval_id or pending["expires_at"] < time.time():
            return TurnResult("failed", "Unknown or expired approval; request the write again.", [])
        if type(approve) is not bool:
            return TurnResult("failed", "Approval requires an explicit boolean decision.", [])
        # Consume before executing: interruption must never replay a potentially committed write.
        await self.sessions.append_event(session, Event(
            author=self.agent.name, actions=EventActions(state_delta={PENDING: None}),
        ))
        if not approve:
            return TurnResult("completed", "Write rejected; nothing was saved.", [])
        operation = pending["operation"]
        turn.authorized_write = _digest(operation)
        result = save_compliance_specification(self.environment_for_state(session.state), **operation)
        await self.sessions.append_event(session, Event(
            author=self.agent.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(result))]),
            actions=EventActions(state_delta=dict(session.state)),
        ))
        return TurnResult("completed" if result.get("saved") else "failed", json.dumps(result), [result])

    async def cancel(self, session_id: str) -> None:
        task = self._active.get(session_id)
        if task is not None:
            task.cancel()

    async def close(self) -> None:
        tasks = list(self._active.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.sessions.close()
