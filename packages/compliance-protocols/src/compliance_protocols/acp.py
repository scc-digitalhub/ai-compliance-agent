"""Agent Client Protocol stdio adapter; client MCP servers are deliberately unsupported."""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from contextlib import redirect_stdout
from typing import Any

from acp import (
    Agent, Client, PROTOCOL_VERSION, RequestError, run_agent, stdio_streams,
    start_tool_call, update_agent_message_text, update_tool_call, update_user_message_text,
)
from acp.schema import (
    AgentCapabilities, Implementation, InitializeResponse, LoadSessionResponse,
    NewSessionResponse, PermissionOption, PromptResponse, ToolCallUpdate,
)

from compliance_core.version import framework_version

from .config import ProtocolSettings
from .runtime import ConversationRuntime


class ComplianceACPAgent(Agent):
    def __init__(self, runtime: ConversationRuntime):
        self.runtime = runtime
        self.client: Client | None = None
        self.initialized = False
        self.sessions: set[str] = set()

    def on_connect(self, conn: Client) -> None:
        self.client = conn

    async def initialize(self, protocol_version: int, client_capabilities=None, client_info=None, **kwargs):
        self.initialized = True
        return InitializeResponse(
            protocolVersion=PROTOCOL_VERSION,
            agentCapabilities=AgentCapabilities(loadSession=True),
            agentInfo=Implementation(name="ai-compliance", version=framework_version()),
        )

    def _ready(self) -> Client:
        if not self.initialized or self.client is None:
            raise RequestError(-32600, "Initialize the ACP connection first")
        return self.client

    def _session(self, session_id: str) -> Client:
        client = self._ready()
        if session_id not in self.sessions:
            raise RequestError(-32602, "Create or load this session before using it")
        return client

    def _cwd(self, cwd: str, mcp_servers, additional_directories) -> str:
        self._ready()
        if not Path(cwd).is_absolute() or not Path(cwd).is_dir():
            raise RequestError(-32602, "cwd must be an existing absolute directory")
        if mcp_servers or additional_directories:
            raise RequestError(-32602, "Client-provided MCP servers and additional directories are not supported")
        return str(Path(cwd).resolve())

    async def new_session(self, cwd: str, mcp_servers=None, additional_directories=None, **kwargs):
        cwd = self._cwd(cwd, mcp_servers, additional_directories)
        session_id = await self.runtime.create(cwd)
        self.sessions.add(session_id)
        return NewSessionResponse(sessionId=session_id)

    async def load_session(self, cwd: str, session_id: str, mcp_servers=None, additional_directories=None, **kwargs):
        cwd = self._cwd(cwd, mcp_servers, additional_directories)
        try:
            session = await self.runtime.get(session_id)
        except ValueError as exc:
            raise RequestError(-32602, str(exc)) from exc
        if session.state.get("protocol_cwd") != cwd:
            raise RequestError(-32602, "The session belongs to a different working directory")
        client = self._ready()
        for item in await self.runtime.history(session_id):
            update = update_user_message_text(item["text"]) if item["role"] == "user" else update_agent_message_text(item["text"])
            await client.session_update(session_id=session_id, update=update)
        self.sessions.add(session_id)
        return LoadSessionResponse()

    async def prompt(self, session_id: str, prompt: list, **kwargs):
        client = self._session(session_id)
        if not prompt or any(block.type != "text" for block in prompt):
            raise RequestError(-32602, "Only non-empty text prompts are supported")
        text = "\n".join(block.text for block in prompt)
        if not text.strip():
            raise RequestError(-32602, "A non-empty text prompt is required")

        async def notify(event: dict[str, Any]) -> None:
            if event["type"] == "text":
                update = update_agent_message_text(event["text"])
            elif event["type"] == "tool_start":
                update = start_tool_call(event["id"], event["name"], status="in_progress")
            else:
                result = event["result"]
                update = update_tool_call(
                    event["id"], status="failed" if isinstance(result, dict) and "error" in result else "completed",
                    raw_output=result,
                )
            await client.session_update(session_id=session_id, update=update)

        async def permission(approval: dict[str, Any]) -> bool:
            operation = approval["operation"]
            response = await client.request_permission(
                session_id=session_id,
                tool_call=ToolCallUpdate(
                    toolCallId=approval["id"], title=f"Save {operation['kind']} specification in {operation['project']}",
                    kind="edit", status="pending", rawInput=operation,
                ),
                options=[
                    PermissionOption(optionId="approve", name="Approve this exact write once", kind="allow_once"),
                    PermissionOption(optionId="reject", name="Reject write", kind="reject_once"),
                ],
            )
            return response.outcome.outcome == "selected" and response.outcome.option_id == "approve"

        try:
            result = await self.runtime.prompt(session_id, text, notify, permission=permission)
        except ValueError as exc:
            raise RequestError(-32602, str(exc)) from exc
        if result.status in ("failed", "cancelled"):
            await client.session_update(session_id=session_id, update=update_agent_message_text(result.text))
        if result.artifacts:
            await client.session_update(
                session_id=session_id,
                update=update_agent_message_text("```json\n" + json.dumps(result.artifacts, indent=2) + "\n```"),
            )
        return PromptResponse(
            stopReason="cancelled" if result.status == "cancelled" else "end_turn",
            _meta={"compliance": {"status": result.status, "artifacts": result.artifacts}},
        )

    async def cancel(self, session_id: str, **kwargs) -> None:
        self._session(session_id)
        await self.runtime.cancel(session_id)


async def serve(runtime: ConversationRuntime) -> None:
    reader, writer = await stdio_streams()
    try:
        with redirect_stdout(sys.stderr):
            await run_agent(ComplianceACPAgent(runtime), input_stream=writer, output_stream=reader)
    finally:
        await runtime.close()


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    with redirect_stdout(sys.stderr):
        runtime = ConversationRuntime(ProtocolSettings())
    asyncio.run(serve(runtime))


if __name__ == "__main__":
    main()
