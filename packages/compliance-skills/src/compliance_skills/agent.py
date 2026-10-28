"""Framework-neutral coordinator definition shipped alongside the skills."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

AGENT_PATH = Path(__file__).resolve().parent / "agents" / "compliance-assistant.md"


@dataclass(frozen=True)
class PortableAgent:
    name: str
    description: str
    skills: tuple[str, ...]
    tools: tuple[str, ...]
    instructions: str


def load_agent(path: Path = AGENT_PATH) -> PortableAgent:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Agent file must start with YAML frontmatter: {path}")
    try:
        _, frontmatter, instructions = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"Agent file has incomplete frontmatter: {path}") from exc
    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise ValueError(f"Agent frontmatter must be a mapping: {path}")
    for field in ("name", "description"):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            raise ValueError(f"Agent {field} must be a non-empty string: {path}")
    for field in ("skills", "tools"):
        values = metadata.get(field)
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError(f"Agent {field} must be a non-empty list of names: {path}")
        if len(values) != len(set(values)):
            raise ValueError(f"Agent {field} must not contain duplicate names: {path}")
    if not instructions.strip():
        raise ValueError(f"Agent instructions must not be empty: {path}")
    return PortableAgent(
        name=metadata["name"],
        description=metadata["description"],
        skills=tuple(metadata["skills"]),
        tools=tuple(metadata["tools"]),
        instructions=instructions.strip(),
    )
