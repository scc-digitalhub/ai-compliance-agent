# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from acp import PROTOCOL_VERSION, RequestError, spawn_agent_process, text_block
from acp.schema import AllowedOutcome, RequestPermissionResponse

from compliance_protocols.acp import ComplianceACPAgent

from protocol_test_support import LOAD_SPECS, SAVE


class Client:
    def __init__(self, approve=False):
        self.updates, self.permissions = [], []
        self.approve = approve

    async def session_update(self, session_id, update, **kwargs):
        self.updates.append(update)

    async def request_permission(self, session_id, tool_call, options, **kwargs):
        self.permissions.append(tool_call)
        return RequestPermissionResponse(outcome=AllowedOutcome(
            outcome="selected", optionId="approve" if self.approve else "reject",
        ))


def test_acp_session_prompt_load_and_capability_policy(runtime_factory, tmp_path):
    async def scenario():
        runtime = runtime_factory(["Hello.", "Continued."])
        client = Client()
        agent = ComplianceACPAgent(runtime)
        agent.on_connect(client)
        try:
            with pytest.raises(RequestError):
                await agent.new_session(str(tmp_path))
            initialization = await agent.initialize(PROTOCOL_VERSION)
            assert initialization.agent_capabilities.load_session
            assert not initialization.agent_capabilities.mcp_capabilities.http
            with pytest.raises(RequestError):
                await agent.new_session(str(tmp_path), mcp_servers=[{"command": "unsafe"}])
            with pytest.raises(RequestError):
                await agent.new_session("relative")
            session = await agent.new_session(str(tmp_path))
            response = await agent.prompt(session.session_id, [text_block("Hi")])
            assert response.stop_reason == "end_turn"
            assert any(getattr(update, "content", None).text == "Hello." for update in client.updates)
            other = ComplianceACPAgent(runtime)
            other.on_connect(client)
            await other.initialize(PROTOCOL_VERSION)
            with pytest.raises(RequestError):
                await other.prompt(session.session_id, [text_block("Do not load implicitly")])
            await other.load_session(str(tmp_path), session.session_id)
            assert (await other.prompt(session.session_id, [text_block("Continue")])).stop_reason == "end_turn"
        finally:
            await runtime.close()
    asyncio.run(scenario())


@pytest.mark.parametrize("approve", [True, False])
def test_acp_permission_gate(runtime_factory, tmp_path, approve):
    async def scenario():
        runtime = runtime_factory([LOAD_SPECS, SAVE, "Done."], allow_writes=True)
        agent = ComplianceACPAgent(runtime)
        client = Client(approve=approve)
        agent.on_connect(client)
        try:
            await agent.initialize(PROTOCOL_VERSION)
            session = await agent.new_session(str(tmp_path))
            await agent.prompt(session.session_id, [text_block("Save scorer in credit")])
            assert len(client.permissions) == 1
            assert client.permissions[0].raw_input["project"] == "credit"
            assert bool(runtime.specifications.data) is approve
        finally:
            await runtime.close()
    asyncio.run(scenario())


def test_acp_real_stdio_exchange(tmp_path):
    async def scenario():
        script = Path(__file__).with_name("stdio_agent.py")
        client = Client()
        async with spawn_agent_process(client, sys.executable, str(script), str(tmp_path)) as (connection, process):
            initialized = await connection.initialize(protocol_version=PROTOCOL_VERSION)
            assert initialized.agent_info.name == "ai-compliance"
            session = await connection.new_session(cwd=str(tmp_path), mcp_servers=[])
            response = await connection.prompt(session_id=session.session_id, prompt=[text_block("Hello")])
            assert response.stop_reason == "end_turn"
            assert any(getattr(update, "content", None).text == "Hello over stdio." for update in client.updates)
            assert process.returncode is None
    asyncio.run(scenario())
