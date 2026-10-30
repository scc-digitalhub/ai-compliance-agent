from __future__ import annotations

import asyncio
from typing import Any

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.config import Settings
from compliance_protocols.config import ProtocolSettings
from compliance_protocols.runtime import ConversationRuntime


class ScriptedLlm(BaseLlm):
    model: str = "scripted"
    script: list[Any]
    delay: float = 0

    async def generate_content_async(self, llm_request, stream=False):
        await asyncio.sleep(self.delay)
        item = self.script.pop(0)
        if isinstance(item, dict):
            part = types.Part(function_call=types.FunctionCall(name=item["call"], args=item.get("args", {})))
        else:
            part = types.Part(text=item)
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


class MemorySpecifications:
    def __init__(self):
        self.data = {}
        self.calls = []

    def get(self, kind, entity, project=None):
        self.calls.append(("get", kind, entity, project))
        return self.data.get((kind, entity, project), {})

    def save(self, kind, entity, specification, project=None):
        self.calls.append(("save", kind, entity, project))
        self.data[(kind, entity, project)] = specification


class MemoryEntities:
    def __init__(self):
        self.calls = []

    def get(self, kind, entity, project=None):
        self.calls.append((kind, entity, project))
        return {"name": entity, "project": project}


@pytest.fixture
def runtime_factory(tmp_path):
    def create(script, **overrides):
        settings = ProtocolSettings(
            state_dir=tmp_path,
            bearer_token="test-token-" + "x" * 32, **overrides,
        )
        agent = build_coordinator_agent(
            Settings(coordinator_model="scripted"), model=ScriptedLlm(script=list(script)),
        )
        return ConversationRuntime(
            settings, agent=agent, specifications=MemorySpecifications(), entities=MemoryEntities(),
        )
    return create


async def noop(event):
    pass


GET_ENTITY = {"call": "get_entity_details", "args": {"kind": "model", "entity": "scorer", "project": "credit"}}
SAVE = {
    "call": "save_compliance_specification",
    "args": {"kind": "model", "entity": "scorer", "project": "credit", "specification": {"objectives": []}},
}
LOAD_ENTITY = {"call": "load_skill", "args": {"skill_name": "entity-details"}}
LOAD_SPECS = {"call": "load_skill", "args": {"skill_name": "compliance-specifications"}}
