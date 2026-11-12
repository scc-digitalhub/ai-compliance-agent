# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from compliance_skills import load_agent
from compliance_adk.agents.coordinator import (
    COORDINATOR_SKILLS,
    INSTRUCTION,
    build_coordinator_agent,
)
from compliance_adk.agents.coordinator_tools import COORDINATOR_TOOLS
from compliance_adk.skill_loader import TOOL_REGISTRY


def test_adk_coordinator_uses_the_portable_definition():
    definition = load_agent()
    assert COORDINATOR_SKILLS == definition.skills
    assert INSTRUCTION == definition.instructions
    available = {fn.__name__ for fn in COORDINATOR_TOOLS} | set(TOOL_REGISTRY)
    assert set(definition.tools) <= available
    agent = build_coordinator_agent(model="gemini-2.0-flash")
    assert agent.name == "compliance_agent"
    assert agent.description == definition.description
    assert callable(agent.instruction)
    assert agent.instruction(None) == definition.instructions
