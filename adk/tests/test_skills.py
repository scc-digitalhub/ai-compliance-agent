# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

import pytest
from google.adk.tools import FunctionTool

from compliance_adk.skill_loader import TOOL_REGISTRY, load_skill, render_instruction, skill_tool_names, skill_tools
from compliance_adk.agents.tool_adapter import workspace_input_reader

from .conftest import SKILLS

SKILL_NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())


def test_skills_are_discovered():
    assert SKILL_NAMES == [
        "compliance-framework",
        "compliance-report",
        "compliance-specifications",
        "dataset-analysis",
        "entity-details",
        "metric-evaluation-code",
        "model-analysis",
        "project-context",
    ]


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_declared_tools_exist(name):
    skill = load_skill(name)
    assert set(skill_tool_names(skill)) <= set(TOOL_REGISTRY)
    assert len(skill_tools(skill)) == len(skill_tool_names(skill))


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_tool_allowlist_uses_portable_frontmatter(name):
    skill = load_skill(name)
    declared = set(skill_tool_names(skill))

    assert isinstance(skill.frontmatter.allowed_tools, str)
    assert declared <= set(skill.frontmatter.allowed_tools.split())
    assert isinstance(skill.frontmatter.metadata["compliance-tools"], str)


@pytest.mark.parametrize(
    "name",
    [
        "project-context",
        "dataset-analysis",
        "model-analysis",
        "metric-evaluation-code",
        "compliance-report",
    ],
)
def test_host_driven_adk_skill_tools_hide_runtime_context(name):
    skill = load_skill(name)
    for fn in skill_tools(skill):
        declaration = FunctionTool(fn)._get_declaration()
        schema = declaration.parameters_json_schema or declaration.parameters
        assert "tool_context" not in str(schema)


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_tools_named_in_procedure_are_allowed(name):
    skill = load_skill(name)
    mentioned = set(re.findall(r"\b(get_\w+|read_okf_concept|list_okf_directory|search_catalog|list_all_concepts)\b", skill.instructions))
    mentioned &= set(TOOL_REGISTRY)
    assert mentioned <= set(skill_tool_names(skill)), mentioned - set(skill_tool_names(skill))


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_no_schema_copies_inside_skills(name):
    assert not list((SKILLS / name).rglob("*.py"))


def test_instruction_embeds_example_unescaped():
    text = render_instruction(load_skill("project-context"))
    assert "Example of a valid output object" in text and '"assumptions"' in text


def test_adk_input_reader_is_workspace_bounded(tmp_path):
    reader = workspace_input_reader(tmp_path)
    (tmp_path / "results.json").write_bytes(b"{}")
    assert reader("results.json") == b"{}"
    with pytest.raises(ValueError, match="workspace-relative"):
        reader("../outside.json")
    with pytest.raises(ValueError, match="workspace-relative"):
        reader("https://example.invalid/results.json")
    with pytest.raises(ValueError, match="limit"):
        (tmp_path / "large.json").write_bytes(b"x" * 1_000_001)
        reader("large.json")
