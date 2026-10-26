from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from compliance_adk.agents.coordinator import COORDINATOR_SKILLS, INSTRUCTION, build_coordinator_agent
from compliance_adk.agents.coordinator_tools import get_session_analyses
from compliance_adk.agents.entity_tools import ENTITY_TOOL_REGISTRY, get_entity_details
from compliance_adk.agents.session_state import DATASETS_KEY, ENTITIES_KEY
from compliance_adk.dh import tools as dh
from compliance_adk.skill_loader import TOOL_REGISTRY, load_skill

from .conftest import ScriptedLlm, example

DATASET_DETAILS = {
    "name": "applications-2024",
    "kind": "table",
    "metadata": {"description": "Loan applications received in 2024"},
    "spec": {"schema": {"fields": [{"name": "age", "type": "integer"}, {"name": "income", "type": "number"}]}},
}
MODEL_DETAILS = {"name": "credit-model", "kind": "sklearn", "spec": {"framework": "sklearn", "algorithm": "xgboost"}}


@pytest.fixture
def dh_entities(monkeypatch):
    """In-memory stand-in for the DH platform entities; keys are (entity kind, entity name)."""
    store: dict[tuple[str, str], dict] = {
        ("dataset", "applications-2024"): dict(DATASET_DETAILS),
        ("model", "credit-model"): dict(MODEL_DETAILS),
    }
    calls: list[tuple[str, str]] = []

    def get_entity(entity, entity_kind):
        calls.append((entity, entity_kind))
        return store.get((entity_kind, entity), {})

    monkeypatch.setattr(dh, "get_entity", get_entity)
    # no specification is stored, so analyses always run
    monkeypatch.setattr(dh, "get_entity_extension", lambda *a: {})
    monkeypatch.setattr(dh, "get_project_extension", lambda *a: {})
    return SimpleNamespace(data=store, calls=calls)


def ctx(**state) -> SimpleNamespace:
    return SimpleNamespace(state=dict(state))


@pytest.mark.parametrize(
    "kind, entity, details", [("dataset", "applications-2024", DATASET_DETAILS), ("model", "credit-model", MODEL_DETAILS)]
)
def test_details_are_retrieved_from_dh_and_kept_in_the_session(dh_entities, kind, entity, details):
    tool_context = ctx()

    out = get_entity_details(kind, entity, tool_context)

    assert out == {"kind": kind, "entity": entity, "source": "dh", "details": details}
    assert dh_entities.calls == [(entity, kind)]
    assert tool_context.state[ENTITIES_KEY] == {kind: {entity: details}}


def test_later_calls_reuse_the_session_without_calling_dh(dh_entities):
    tool_context = ctx()
    get_entity_details("dataset", "applications-2024", tool_context)
    dh_entities.data[("dataset", "applications-2024")] = {**DATASET_DETAILS, "metadata": {"description": "changed"}}

    out = get_entity_details("dataset", "applications-2024", tool_context)

    assert out["source"] == "session"
    assert out["details"]["metadata"]["description"] == "Loan applications received in 2024"
    assert len(dh_entities.calls) == 1


def test_refresh_reloads_the_details_from_dh(dh_entities):
    tool_context = ctx()
    get_entity_details("dataset", "applications-2024", tool_context)
    dh_entities.data[("dataset", "applications-2024")] = {**DATASET_DETAILS, "metadata": {"description": "changed"}}

    out = get_entity_details("dataset", "applications-2024", tool_context, refresh=True)

    assert out["source"] == "dh" and out["details"]["metadata"]["description"] == "changed"
    assert tool_context.state[ENTITIES_KEY]["dataset"]["applications-2024"]["metadata"]["description"] == "changed"
    assert len(dh_entities.calls) == 2


def test_entities_of_both_kinds_coexist_in_the_session(dh_entities):
    tool_context = ctx(**{DATASETS_KEY: {"other": {"kept": True}}})

    get_entity_details("dataset", "applications-2024", tool_context)
    get_entity_details("model", "credit-model", tool_context)

    entities = get_session_analyses(tool_context)["entities"]
    assert set(entities) == {"dataset", "model"}
    assert set(entities["dataset"]) == {"applications-2024"} and set(entities["model"]) == {"credit-model"}
    assert tool_context.state[DATASETS_KEY] == {"other": {"kept": True}}  # analyses are untouched


def test_missing_entity_is_reported_and_not_cached(dh_entities):
    tool_context = ctx()

    out = get_entity_details("model", "unknown", tool_context)

    assert out["code"] == "not_found"
    assert ENTITIES_KEY not in tool_context.state


def test_platform_failures_are_returned_not_raised(monkeypatch):
    def boom(entity, entity_kind):
        raise ConnectionError("unreachable")

    monkeypatch.setattr(dh, "get_entity", boom)
    tool_context = ctx()

    out = get_entity_details("dataset", "applications-2024", tool_context)

    assert out["code"] == "dh_error" and "unreachable" in out["error"]
    assert tool_context.state == {}


def test_unknown_kind_is_rejected(dh_entities):
    assert get_entity_details("project", "x", ctx())["code"] == "invalid_kind"
    assert dh_entities.calls == []


def test_tool_is_registered_and_its_declaration_builds():
    assert ENTITY_TOOL_REGISTRY["get_entity_details"] is TOOL_REGISTRY["get_entity_details"]
    declaration = FunctionTool(get_entity_details)._get_declaration()
    schema = str(declaration.parameters_json_schema or declaration.parameters)
    assert "tool_context" not in schema
    assert all(word in schema for word in ("dataset", "model", "refresh"))


def test_guidance_tells_the_agent_to_reuse_and_refresh_only_on_request():
    skill = load_skill("entity-details").instructions
    assert "entity-details" in COORDINATOR_SKILLS
    assert "get_entity_details" in skill and "refresh=True" in skill and "not_found" in skill
    assert "entity-details" in INSTRUCTION and "get_entity_details" in INSTRUCTION and "refresh=True" in INSTRUCTION


LOAD_SKILL = {"call": "load_skill", "args": {"skill_name": "entity-details"}}
GET_DATASET = {"call": "get_entity_details", "args": {"kind": "dataset", "entity": "applications-2024"}}
REFRESH_DATASET = {**GET_DATASET, "args": {**GET_DATASET["args"], "refresh": True}}
ANALYSE_DATASET = {
    "call": "analyze_dataset",
    "args": {"dataset": {"name": "applications-2024", "scope": "TRAINING", "description": "Loan applications received in 2024"}},
}


def run_turns(agent, *prompts):
    async def chat():
        sessions = InMemorySessionService()
        runner = Runner(agent=agent, app_name="t", session_service=sessions)
        session = await sessions.create_session(app_name="t", user_id="u")
        turns = []
        for prompt in prompts:
            message = types.Content(role="user", parts=[types.Part(text=prompt)])
            turns.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=message)])
        return turns, await sessions.get_session(app_name="t", user_id="u", session_id=session.id)

    return asyncio.run(chat())


def responses(events, name) -> list[dict]:
    return [
        p.function_response.response
        for e in events
        if e.content
        for p in e.content.parts
        if p.function_response and p.function_response.name == name
    ]


def test_coordinator_analyses_a_dataset_by_name_end_to_end(make_registry, settings, dh_entities):
    _, analysis_llm = make_registry(example("dataset-analysis"))
    agent = build_coordinator_agent(
        settings,
        model=ScriptedLlm(script=[LOAD_SKILL, GET_DATASET, ANALYSE_DATASET, "Dataset analysed."], seen_messages=[]),
    )

    (turn,), session = run_turns(agent, "Run the compliance analysis of dataset applications-2024")

    assert turn[-1].content.parts[0].text == "Dataset analysed."
    assert responses(turn, "get_entity_details")[0]["details"] == DATASET_DETAILS
    assert "data" in responses(turn, "analyze_dataset")[0]
    assert len(analysis_llm.seen_messages) == 1 and "applications-2024" in analysis_llm.seen_messages[0]
    assert session.state[ENTITIES_KEY]["dataset"]["applications-2024"] == DATASET_DETAILS
    assert "applications-2024" in session.state[DATASETS_KEY]


def test_coordinator_reuses_details_across_turns_and_refreshes_on_request(settings, dh_entities):
    agent = build_coordinator_agent(
        settings,
        model=ScriptedLlm(
            script=[LOAD_SKILL, GET_DATASET, "Found it.", GET_DATASET, "Same as before.", REFRESH_DATASET, "Refreshed."],
            seen_messages=[],
        ),
    )

    (first, second, third), session = run_turns(
        agent, "Get dataset applications-2024", "Show it again", "Refresh it, it changed on the platform"
    )

    assert responses(first, "get_entity_details")[0]["source"] == "dh"
    assert responses(second, "get_entity_details")[0]["source"] == "session"
    assert responses(third, "get_entity_details")[0]["source"] == "dh"
    assert len(dh_entities.calls) == 2  # the second turn did not call the platform
