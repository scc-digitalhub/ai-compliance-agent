# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Framework-neutral loader for packaged Agent Skills."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SKILLS_PATH = Path(__file__).resolve().parent / "skills"


@dataclass(frozen=True)
class PortableSkill:
    name: str
    description: str
    instructions: str
    allowed_tools: tuple[str, ...]
    metadata: dict[str, str]


def load_skill(name: str, root: Path = SKILLS_PATH) -> PortableSkill:
    if not name or Path(name).name != name:
        raise ValueError(f"Invalid skill name: {name!r}")

    path = root / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Skill file must start with YAML frontmatter: {path}")
    try:
        _, frontmatter, instructions = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"Skill file has incomplete frontmatter: {path}") from exc

    metadata: Any = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise ValueError(f"Skill frontmatter must be a mapping: {path}")
    name_value = metadata.get("name")
    description = metadata.get("description")
    tools = metadata.get("allowed-tools", "")
    extra = metadata.get("metadata", {})
    if name_value != name or not isinstance(description, str) or not description:
        raise ValueError(f"Skill frontmatter name/description is invalid: {path}")
    if not isinstance(tools, str) or not isinstance(extra, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in extra.items()
    ):
        raise ValueError(f"Skill frontmatter tools/metadata are invalid: {path}")

    return PortableSkill(
        name=name,
        description=description,
        instructions=instructions.strip(),
        allowed_tools=tuple(tools.split()),
        metadata=extra,
    )


__all__ = ["PortableSkill", "SKILLS_PATH", "load_skill"]
