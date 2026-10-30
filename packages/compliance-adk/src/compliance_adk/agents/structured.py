"""Factory for the structured (stateless, schema-bound) agents."""
from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.tools import FunctionTool
from google.genai import types

from compliance_core.analysis_engine import ANALYST_INSTRUCTIONS

from ..config import Settings, get_settings
from ..skill_loader import load_skill, render_instruction, skill_tools
from .llm import build_llm, build_planner
from .specs import StructuredAgentSpec

ROLE_PROMPT = ANALYST_INSTRUCTIONS


def build_structured_agent(
    spec: StructuredAgentSpec,
    settings: Settings | None = None,
    model: BaseLlm | str | None = None,
) -> LlmAgent:
    settings = settings or get_settings()
    skill = load_skill(spec.skill_name)
    instruction = f"{ROLE_PROMPT}\n{render_instruction(skill)}"
    return LlmAgent(
        name=spec.agent_name,
        model=model or build_llm(spec.role, settings),
        description=spec.description,
        # A provider function skips {var} state injection, which would choke on the JSON example.
        instruction=lambda _ctx: instruction,
        tools=[FunctionTool(fn) for fn in skill_tools(skill)],
        # No input_schema: ADK validates every user turn against it, including retry feedback.
        # The request is validated by spec.input_schema before the agent runs.
        output_schema=spec.output_schema,
        output_key=spec.output_key,
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        planner=build_planner(settings.structured_thinking_budget),
        generate_content_config=(
            types.GenerateContentConfig(temperature=settings.structured_temperature)
            if settings.structured_temperature is not None
            else None
        ),
    )
