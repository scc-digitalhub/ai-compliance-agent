# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""LLM and planner construction from settings."""
from __future__ import annotations

from google.adk.models.lite_llm import LiteLlm
from google.adk.planners import BuiltInPlanner
from google.genai import types

from ..config import ModelRole, Settings, get_settings


def build_llm(role: ModelRole, settings: Settings | None = None) -> LiteLlm:
    settings = settings or get_settings()
    kwargs: dict[str, str] = {}
    if settings.llm_api_base:
        kwargs["api_base"] = settings.llm_api_base
    if settings.llm_api_key:
        kwargs["api_key"] = settings.llm_api_key.get_secret_value()
    return LiteLlm(model=settings.model_name_for(role), **kwargs)


def build_planner(thinking_budget: int | None) -> BuiltInPlanner | None:
    """Thinking is a provider feature; only enabled when a budget is configured."""
    if thinking_budget is None:
        return None
    return BuiltInPlanner(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=thinking_budget)
    )
