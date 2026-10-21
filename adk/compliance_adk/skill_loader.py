"""Loads skills from disk; a skill's metadata is the single source of its tool allowlist."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Callable

from google.adk.skills import load_skill_from_dir
from google.adk.skills.models import Skill

from .config import get_settings
from .errors import ConfigError
from .knowledge.tools import TOOL_REGISTRY

EXAMPLE_REFERENCE = "example.json"


@lru_cache
def load_skill(name: str) -> Skill:
    return load_skill_from_dir(get_settings().skills_path / name)


def skill_tool_names(skill: Skill) -> list[str]:
    return list(skill.frontmatter.metadata.get("adk_additional_tools", []))


def skill_tools(skill: Skill) -> list[Callable[..., Any]]:
    unknown = [n for n in skill_tool_names(skill) if n not in TOOL_REGISTRY]
    if unknown:
        raise ConfigError(f"Skill '{skill.name}' declares unknown tools: {unknown}")
    return [TOOL_REGISTRY[n] for n in skill_tool_names(skill)]


def render_instruction(skill: Skill) -> str:
    """Skill body plus its example result, as one instruction text."""
    text = skill.instructions.strip()
    example = skill.resources.references.get(EXAMPLE_REFERENCE)
    if example:
        pretty = json.dumps(json.loads(example), indent=2, ensure_ascii=False)
        text += f"\n\nExample of a valid output object:\n{pretty}"
    return text
