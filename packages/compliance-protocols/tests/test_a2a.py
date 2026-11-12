# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import uuid
import json

import httpx
import pytest

from compliance_protocols.a2a import create_app
from compliance_protocols.config import ProtocolSettings
from a2a.server.context import ServerCallContext
from a2a.types import Task, TaskStatus, TaskState

from protocol_test_support import LOAD_SPECS, SAVE


async def rpc(client, method, params):
    response = await client.post("/a2a", headers={"A2A-Version": "1.0"}, json={
        "jsonrpc": "2.0", "id": uuid.uuid4().hex, "method": method, "params": params,
    })
    assert response.status_code == 200, response.text
    return response.json()


def message(text=None, *, context_id=None, task_id=None, data=None):
    msg = {
        "messageId": uuid.uuid4().hex, "role": "ROLE_USER",
        "parts": [{"text": text}] if text is not None else [{"data": data}],
    }
    if context_id:
        msg["contextId"] = context_id
    if task_id:
        msg["taskId"] = task_id
    return {"message": msg}


def test_a2a_requires_bearer_configuration():
    with pytest.raises(ValueError, match="BEARER_TOKEN"):
        create_app(ProtocolSettings(bearer_token=None))


def test_a2a_discovery_authentication_and_jsonrpc(runtime_factory):
    async def scenario():
        runtime = runtime_factory(["Hello from A2A."])
        app = create_app(runtime.settings, runtime=runtime)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                card = (await client.get("/.well-known/agent-card.json")).json()
                assert card["name"] == "compliance-assistant"
                assert card["capabilities"]["streaming"]
                assert "bearer" in card["securitySchemes"]
                assert (await client.post("/a2a", json={})).status_code == 401
                client.headers["Authorization"] = "Bearer " + runtime.settings.bearer_token.get_secret_value()
                result = await rpc(client, "SendMessage", message("Hello"))
                assert "error" not in result, result
                task = result["result"]["task"]
                assert task["status"]["state"] == "TASK_STATE_COMPLETED"
                assert task["status"]["message"]["parts"][0]["text"] == "Hello from A2A."
                fetched = await rpc(client, "GetTask", {"id": task["id"]})
                assert fetched["result"]["id"] == task["id"]
    asyncio.run(scenario())


def test_a2a_input_required_and_write_approval(runtime_factory):
    async def scenario():
        runtime = runtime_factory([LOAD_SPECS, SAVE, "Please approve this exact write."], allow_writes=True)
        app = create_app(runtime.settings, runtime=runtime)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test",
                headers={"Authorization": "Bearer " + runtime.settings.bearer_token.get_secret_value()},
            ) as client:
                first = await rpc(client, "SendMessage", message("Save model scorer in credit"))
                assert "error" not in first, first
                task = first["result"]["task"]
                assert task["status"]["state"] == "TASK_STATE_INPUT_REQUIRED"
                assert runtime.specifications.data == {}
                session = await runtime.get(task["contextId"])
                approval_id = session.state["protocol_pending_write"]["id"]
                second = await rpc(client, "SendMessage", message(
                    context_id=task["contextId"], task_id=task["id"],
                    data={"approval_id": approval_id, "approve": True},
                ))
                assert "error" not in second, second
                assert second["result"]["task"]["status"]["state"] == "TASK_STATE_COMPLETED"
                assert second["result"]["task"]["artifacts"]
                assert runtime.specifications.data
    asyncio.run(scenario())


def test_a2a_task_and_conversation_survive_restart(runtime_factory):
    async def scenario():
        runtime = runtime_factory(["Persisted."])
        app = create_app(runtime.settings, runtime=runtime)
        headers = {"Authorization": "Bearer " + runtime.settings.bearer_token.get_secret_value()}
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers=headers) as client:
                first = await rpc(client, "SendMessage", message("Remember this"))
                assert "error" not in first, first
                task = first["result"]["task"]
        restored = runtime_factory(["Continued."])
        app = create_app(restored.settings, runtime=restored)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers=headers) as client:
                fetched = await rpc(client, "GetTask", {"id": task["id"]})
                assert fetched["result"]["status"]["state"] == "TASK_STATE_COMPLETED"
                assert any(item["text"] == "Remember this" for item in await restored.history(task["contextId"]))
                second = await rpc(client, "SendMessage", message("Continue", context_id=task["contextId"]))
                assert "error" not in second, second
                assert second["result"]["task"]["contextId"] == task["contextId"]
    asyncio.run(scenario())


def test_a2a_streaming_and_interrupted_task_recovery(runtime_factory):
    async def scenario():
        runtime = runtime_factory(["Streamed answer."])
        app = create_app(runtime.settings, runtime=runtime)
        store = app.state.task_store
        await store.initialize()
        await store.save(
            Task(id="interrupted", context_id="old", status=TaskStatus(state=TaskState.TASK_STATE_WORKING)),
            ServerCallContext(),
        )
        async with app.router.lifespan_context(app):
            recovered = await store.get("interrupted", ServerCallContext())
            assert recovered.status.state == TaskState.TASK_STATE_FAILED
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test",
                headers={"Authorization": "Bearer " + runtime.settings.bearer_token.get_secret_value()},
            ) as client:
                response = await client.post("/a2a", headers={"A2A-Version": "1.0"}, json={
                    "jsonrpc": "2.0", "id": "stream", "method": "SendStreamingMessage",
                    "params": message("Hello"),
                })
                assert response.status_code == 200
                assert "text/event-stream" in response.headers["content-type"]
                events = [
                    json.loads(line.removeprefix("data: "))
                    for line in response.text.splitlines() if line.startswith("data: ")
                ]
                assert events
                assert "TASK_STATE_COMPLETED" in response.text
                assert "Streamed answer." in response.text
    asyncio.run(scenario())


@pytest.mark.parametrize("wait_until_running", [False, True])
def test_a2a_cancels_an_active_task(runtime_factory, wait_until_running):
    async def scenario():
        runtime = runtime_factory(["Slow result."])
        runtime.agent.model.delay = 2
        app = create_app(runtime.settings, runtime=runtime)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test",
                headers={"Authorization": "Bearer " + runtime.settings.bearer_token.get_secret_value()},
            ) as client:
                params = message("Wait")
                params["configuration"] = {"returnImmediately": True}
                first = await rpc(client, "SendMessage", params)
                assert "error" not in first, first
                task = first["result"]["task"]
                if wait_until_running:
                    async with asyncio.timeout(2):
                        while task["contextId"] not in runtime._active:
                            await asyncio.sleep(0.01)
                result = await rpc(client, "CancelTask", {"id": task["id"]})
                assert "error" not in result, result
                assert result["result"]["status"]["state"] == "TASK_STATE_CANCELED"
    asyncio.run(scenario())
