from __future__ import annotations

import re

import pytest

from compliance_adk.skill_loader import TOOL_REGISTRY, load_skill, render_instruction, skill_tool_names, skill_tools

from .conftest import SKILLS

SKILL_NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())


def test_skills_are_discovered():
    assert SKILL_NAMES == [
        "compliance-framework",
        "compliance-specifications",
        "dataset-analysis",
        "entity-details",
        "model-analysis",
        "project-context",
    ]


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_declared_tools_exist(name):
    skill = load_skill(name)
    assert set(skill_tool_names(skill)) <= set(TOOL_REGISTRY)
    assert len(skill_tools(skill)) == len(skill_tool_names(skill))


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
