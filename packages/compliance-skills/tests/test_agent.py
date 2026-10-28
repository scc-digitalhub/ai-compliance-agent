from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from compliance_skills import AGENT_PATH, SKILLS_PATH, load_agent, load_skill
from compliance_core.tool_catalog import TOOL_SPECS


def test_agent_declares_existing_skills_and_tools():
    agent = load_agent()
    assert agent.name == "compliance-assistant"
    assert set(agent.skills) == {path.name for path in SKILLS_PATH.iterdir() if path.is_dir()}
    tools = set(agent.tools)
    for name in agent.skills:
        tools.update(load_skill(name).allowed_tools)
    assert tools <= {spec.name for spec in TOOL_SPECS}


def test_agent_preserves_coordinator_guardrails():
    instructions = load_agent().instructions
    for rule in (
        "default to host-driven mode",
        "project (name, domain,",
        "dataset (name, scope), model (name, ai_task)",
        "Ask instead of guessing",
        "record_compliance_analysis",
        "Never write to DigitalHub unless the",
        "use rerun=True only after the user confirms",
        "refresh=True only when the user",
        "not get_session_analyses",
        "Never invent catalog ids",
        "not legal advice",
        "user must explicitly identify the project",
        "Never select a project from environment variables",
    ):
        assert rule in instructions


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter",
        "---\nname: incomplete",
        "---\n[]\n---\nInstructions",
        "---\nname: x\n---\nInstructions",
    ],
)
def test_agent_rejects_malformed_frontmatter(tmp_path: Path, text: str):
    path = tmp_path / "agent.md"
    path.write_text(text)
    with pytest.raises(ValueError):
        load_agent(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("description", None),
        ("skills", "project-context"),
        ("skills", []),
        ("skills", ["project-context", "project-context"]),
        ("tools", [1]),
        ("tools", [""]),
    ],
)
def test_agent_rejects_invalid_fields(tmp_path: Path, field: str, value: object):
    _, header, body = AGENT_PATH.read_text().split("---", 2)
    metadata = yaml.safe_load(header)
    metadata[field] = value
    path = tmp_path / "agent.md"
    path.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + body)
    with pytest.raises(ValueError, match=field):
        load_agent(path)


def test_agent_requires_instructions(tmp_path: Path):
    _, header, _ = AGENT_PATH.read_text().split("---", 2)
    path = tmp_path / "agent.md"
    path.write_text("---\n" + header + "---\n")
    with pytest.raises(ValueError, match="instructions"):
        load_agent(path)
