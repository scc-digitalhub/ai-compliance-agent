"""Loads skills from disk; a skill's metadata is the single source of its tool allowlist."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Callable

from google.adk.skills import load_skill_from_dir
from google.adk.skills.models import Skill

from .agents.entity_tools import ENTITY_TOOL_REGISTRY
from .agents.host_tools import HOST_TOOL_REGISTRY
from .agents.knowledge_tools import TOOL_REGISTRY as OKF_TOOL_REGISTRY
from .agents.metric_evaluation_tools import TOOL_REGISTRY as METRIC_EVALUATION_TOOL_REGISTRY
from .agents.report_tools import TOOL_REGISTRY as REPORT_TOOL_REGISTRY
from .agents.specification_tools import SPECIFICATION_TOOL_REGISTRY
from .config import get_settings
from compliance_core.errors import ConfigurationError

EXAMPLE_REFERENCE = "example.json"
TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    **OKF_TOOL_REGISTRY,
    **SPECIFICATION_TOOL_REGISTRY,
    **ENTITY_TOOL_REGISTRY,
    **HOST_TOOL_REGISTRY,
    **METRIC_EVALUATION_TOOL_REGISTRY,
    **REPORT_TOOL_REGISTRY,
}


@lru_cache
def load_skill(name: str) -> Skill:
    skill = load_skill_from_dir(get_settings().skills_path / name)
    metadata = skill.frontmatter.metadata
    if "compliance-tools" in metadata and "adk_additional_tools" not in metadata:
        metadata["adk_additional_tools"] = skill_tool_names(skill)
    return skill


def skill_tool_names(skill: Skill) -> list[str]:
    metadata = skill.frontmatter.metadata
    portable = metadata.get("compliance-tools")
    legacy = metadata.get("adk_additional_tools")
    raw = portable if portable is not None else legacy
    if isinstance(raw, str):
        return [name.strip() for name in raw.split(",") if name.strip()]
    if isinstance(raw, list) and all(isinstance(name, str) for name in raw):
        return raw
    if raw is None:
        return []
    raise ConfigurationError(
        f"Skill '{skill.name}' must declare compliance-tools as a comma-separated string"
    )


def skill_tools(skill: Skill) -> list[Callable[..., Any]]:
    unknown = [n for n in skill_tool_names(skill) if n not in TOOL_REGISTRY]
    if unknown:
        raise ConfigurationError(f"Skill '{skill.name}' declares unknown tools: {unknown}")
    return [TOOL_REGISTRY[n] for n in skill_tool_names(skill)]


def render_instruction(skill: Skill) -> str:
    """Skill body plus its example result, as one instruction text."""
    text = skill.instructions.strip()
    example = skill.resources.references.get(EXAMPLE_REFERENCE)
    if example:
        pretty = json.dumps(json.loads(example), indent=2, ensure_ascii=False)
        text += f"\n\nExample of a valid output object:\n{pretty}"
    return text
