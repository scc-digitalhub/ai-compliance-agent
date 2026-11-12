# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Interactive coordinator: reasons about compliance and runs the structured analyses on request."""
from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.tools import FunctionTool, skill_toolset

from compliance_skills import load_agent

from ..config import Settings, get_settings
from ..skill_loader import load_skill, skill_tools
from .coordinator_tools import COORDINATOR_TOOLS
from .llm import build_llm, build_planner

COORDINATOR_DEFINITION = load_agent()
COORDINATOR_SKILLS = COORDINATOR_DEFINITION.skills
INSTRUCTION = COORDINATOR_DEFINITION.instructions


def build_coordinator_agent(
    settings: Settings | None = None, model: BaseLlm | str | None = None
) -> LlmAgent:
    settings = settings or get_settings()
    skills = [load_skill(name) for name in COORDINATOR_SKILLS]
    return LlmAgent(
        name="compliance_agent",
        model=model or build_llm("coordinator", settings),
        description=COORDINATOR_DEFINITION.description,
        instruction=lambda _ctx: INSTRUCTION,
        tools=[
            skill_toolset.SkillToolset(
                skills=skills,
                additional_tools=[FunctionTool(fn) for skill in skills for fn in skill_tools(skill)],
            ),
            *[FunctionTool(fn) for fn in COORDINATOR_TOOLS],
        ],
        planner=build_planner(settings.coordinator_thinking_budget),
    )
