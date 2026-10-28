"""Authenticated single-tenant A2A 1.0 JSON-RPC service backed by the shared runtime."""
from __future__ import annotations

import asyncio
import hmac
import json
import logging
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import TaskUpdater
from a2a.server.tasks.database_task_store import DatabaseTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentInterface, AgentSkill, HTTPAuthSecurityScheme,
    Part, SecurityRequirement, SecurityScheme, StringList, Task, TaskState, TaskStatus,
    ListTasksRequest,
)
from a2a.server.context import ServerCallContext
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Value
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from compliance_skills import load_agent, load_skill

from .config import ProtocolSettings
from .runtime import ConversationRuntime

logger = logging.getLogger(__name__)


def data_part(data: Any) -> Part:
    return Part(data=ParseDict(data, Value()), media_type="application/json")


class ComplianceExecutor(AgentExecutor):
    def __init__(self, runtime: ConversationRuntime):
        self.runtime = runtime
        self._session_lock = asyncio.Lock()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if not context.task_id or not context.context_id or context.message is None:
            raise ValueError("A task, context and message are required")
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if context.current_task is None:
            await event_queue.enqueue_event(Task(
                id=context.task_id, context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                history=[context.message],
            ))
        await updater.start_work()

        async def notify(event: dict[str, Any]) -> None:
            if event["type"] == "text":
                await updater.start_work(updater.new_agent_message([Part(text=event["text"])]))
            elif event["type"] == "tool_start":
                await updater.start_work(updater.new_agent_message([Part(text=f"Running {event['name']}")]))

        try:
            async with self._session_lock:
                try:
                    await self.runtime.get(context.context_id)
                except ValueError:
                    await self.runtime.create(session_id=context.context_id)
            approval = None
            texts = []
            for part in context.message.parts:
                if part.WhichOneof("content") == "text":
                    texts.append(part.text)
                elif part.WhichOneof("content") == "data":
                    value = MessageToDict(part.data)
                    if isinstance(value, dict) and "approval_id" in value:
                        if set(value) != {"approval_id", "approve"} or not isinstance(value["approval_id"], str) or type(value["approve"]) is not bool:
                            raise ValueError("Approval data requires only approval_id (string) and approve (boolean)")
                        if approval is not None:
                            raise ValueError("Only one approval decision is allowed")
                        approval = value
                    else:
                        texts.append(json.dumps(value))
                else:
                    raise ValueError("Only text and JSON data parts are supported")
            if approval and texts:
                raise ValueError("Send approval decisions separately from prompts")
            result = await self.runtime.prompt(
                context.context_id, "\n".join(texts), notify,
                **(approval or {}),
            )
            for artifact in result.artifacts:
                await updater.add_artifact([data_part(artifact)], name="compliance-result", last_chunk=True)
            parts = [Part(text=result.text or "The agent requires further input.")]
            if result.approval:
                parts.append(data_part({"approval_required": result.approval}))
            message = updater.new_agent_message(parts)
            if result.status == "input_required":
                await updater.requires_input(message)
            elif result.status == "failed":
                await updater.failed(message)
            elif result.status == "cancelled":
                await updater.cancel(message)
            else:
                await updater.complete(message)
        except asyncio.CancelledError:
            await updater.cancel()
            raise
        except ValueError as exc:
            await updater.reject(updater.new_agent_message([Part(text=str(exc))]))
        except Exception:
            logger.exception("A2A execution failed for task %s", context.task_id)
            await updater.failed(updater.new_agent_message([Part(text="Agent execution failed; consult server logs.")]))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # The SDK cancels this task's executor coroutine before invoking this callback.
        if context.task_id and context.context_id:
            await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()


class BearerMiddleware:
    def __init__(self, app, token: str):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] not in ("/.well-known/agent-card.json", "/health"):
            headers = dict(scope.get("headers", []))
            authorization = headers.get(b"authorization", b"")
            if not hmac.compare_digest(authorization, f"Bearer {self.token}".encode()):
                await JSONResponse(
                    {"error": "Bearer authentication required"}, status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )(scope, receive, send)
                return
        await self.app(scope, receive, send)


def build_card(settings: ProtocolSettings) -> AgentCard:
    parsed = urlparse(settings.public_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("public_url must be an absolute HTTP(S) origin without a path")
    definition = load_agent()
    return AgentCard(
        name=definition.name, description=definition.description, version="0.1.0",
        supported_interfaces=[AgentInterface(
            url=settings.public_url.rstrip("/") + "/a2a", protocol_binding="JSONRPC", protocol_version="1.0",
        )],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        skills=[
            AgentSkill(id=name, name=name, description=load_skill(name).description, tags=["compliance"])
            for name in definition.skills
        ],
        security_schemes={"bearer": SecurityScheme(
            http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="Bearer"),
        )},
        security_requirements=[SecurityRequirement(schemes={"bearer": StringList()})],
    )


def create_app(settings: ProtocolSettings | None = None, *, runtime: ConversationRuntime | None = None):
    settings = settings or ProtocolSettings()
    if settings.bearer_token is None or len(settings.bearer_token.get_secret_value()) < 32:
        raise ValueError("Set COMPLIANCE_PROTOCOL_BEARER_TOKEN to a secret of at least 32 characters")
    card = build_card(settings)
    runtime = runtime or ConversationRuntime(settings)
    directory = settings.prepare_directory()
    engine = create_async_engine(f"sqlite+aiosqlite:///{directory / 'tasks.db'}")
    store = DatabaseTaskStore(engine)
    handler = DefaultRequestHandler(
        agent_executor=ComplianceExecutor(runtime), task_store=store,
        agent_card=card, validate_input_modes=True,
    )

    @asynccontextmanager
    async def lifespan(app):
        await store.initialize()
        # A stopped worker cannot resume an in-flight model or a partially committed SDK call.
        for state in (TaskState.TASK_STATE_SUBMITTED, TaskState.TASK_STATE_WORKING):
            cursor = ""
            while True:
                page = await store.list(
                    ListTasksRequest(status=state, page_size=100, page_token=cursor),
                    ServerCallContext(),
                )
                for task in page.tasks:
                    task.status.state = TaskState.TASK_STATE_FAILED
                    task.status.message.parts.add(text="Service restarted during execution; reconcile any pending DigitalHub write before retrying.")
                    await store.save(task, ServerCallContext())
                cursor = page.next_page_token
                if not cursor:
                    break
        try:
            yield
        finally:
            await handler.aclose()
            await runtime.close()
            await engine.dispose()

    async def health(request):
        return JSONResponse({"status": "ok"})

    from starlette.middleware import Middleware
    from starlette.routing import Route

    app = Starlette(
        routes=[
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(handler, "/a2a"),
            Route("/health", health),
        ],
        middleware=[Middleware(BearerMiddleware, token=settings.bearer_token.get_secret_value())],
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.state.task_store = store
    return app


def main() -> None:
    import uvicorn

    settings = ProtocolSettings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, workers=1)


if __name__ == "__main__":
    main()
