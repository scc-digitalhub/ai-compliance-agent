from __future__ import annotations

from compliance_skills import load_agent
from compliance_adk.agents.coordinator import (
    COORDINATOR_SKILLS,
    INSTRUCTION,
    build_coordinator_agent,
)
from compliance_adk.agents.coordinator_tools import COORDINATOR_TOOLS


def test_adk_coordinator_uses_the_portable_definition():
    definition = load_agent()
    assert COORDINATOR_SKILLS == definition.skills
    assert INSTRUCTION == definition.instructions
    assert {fn.__name__ for fn in COORDINATOR_TOOLS} == set(definition.tools)
    agent = build_coordinator_agent(model="gemini-2.0-flash")
    assert agent.name == "compliance_agent"
    assert agent.description == definition.description
    assert callable(agent.instruction)
    assert agent.instruction(None) == definition.instructions
