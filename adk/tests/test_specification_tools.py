from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.agents.session_state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROJECT_KEY
from compliance_adk.agents.specification_tools import (
    SPECIFICATION_TOOL_REGISTRY,
    get_compliance_specification,
    save_compliance_specification,
)
from compliance_adk.contracts import ComplianceContextOut, ProjectComplianceSpec, ProjectInput
from compliance_adk.dh import tools as dh

from .conftest import PROJECT, ScriptedLlm, example


@pytest.fixture
def dh_store(monkeypatch):
    """In-memory stand-in for the DH platform; keys are (entity kind, entity, extension kind)."""
    store: dict[tuple[str, str, str], dict] = {}
    calls: list[tuple] = []

    def get_project(project, extension_kind):
        calls.append(("get_project", project, extension_kind))
        return store.get(("project", project, extension_kind), {})

    def get_entity(entity, entity_kind, extension_kind):
        calls.append(("get_entity", entity, entity_kind, extension_kind))
        return store.get((entity_kind, entity, extension_kind), {})

    def save_project(project, extension_kind, extension):
        calls.append(("save_project", project, extension_kind))
        store[("project", project, extension_kind)] = extension

    def save_entity(entity, entity_kind, extension_kind, extension):
        calls.append(("save_entity", entity, entity_kind, extension_kind))
        store[(entity_kind, entity, extension_kind)] = extension

    monkeypatch.setattr(dh, "get_project_extension", get_project)
    monkeypatch.setattr(dh, "get_entity_extension", get_entity)
    monkeypatch.setattr(dh, "save_project_extension", save_project)
    monkeypatch.setattr(dh, "save_entity_extension", save_entity)
    return SimpleNamespace(data=store, calls=calls)


def ctx(**state) -> SimpleNamespace:
    return SimpleNamespace(state=dict(state))


def project_context():
    return example("project-context")["result"]


def project_state(name: str = PROJECT["name"]) -> dict:
    """Session state after a project analysis."""
    project = ProjectInput(**{**PROJECT, "name": name})
    return {PROJECT_KEY: project.model_dump(mode="json"), CONTEXT_KEY: project_context()}


def project_spec():
    """The ai-compliance extension spec: the project description with the compliance context."""
    spec = ProjectComplianceSpec.of(ProjectInput(**PROJECT), ComplianceContextOut(**project_context()))
    return spec.model_dump(mode="json", exclude_none=True)


def null_paths(value, path="") -> list[str]:
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in null_paths(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for v in value for p in null_paths(v, f"{path}[]")]
    return [path] if value is None else []


def dataset_spec():
    return example("dataset-analysis")["result"]


def model_spec():
    return example("model-analysis")["result"]


def test_save_stores_the_analysed_specifications_under_the_dh_extension_kinds(dh_store):
    tool_context = ctx(
        **{
            **project_state(),
            DATASETS_KEY: {"Applications": dataset_spec()},
            MODELS_KEY: {"Credit model": model_spec()},
        }
    )

    results = [
        save_compliance_specification("project", "credit-scoring", tool_context),
        save_compliance_specification("dataset", "Applications", tool_context),
        save_compliance_specification("model", "Credit model", tool_context),
    ]

    assert all(r["saved"] and r["source"] == "session" for r in results)
    assert set(dh_store.data) == {
        ("project", "credit-scoring", "ai-compliance"),
        ("dataset", "Applications", "data-compliance"),
        ("model", "Credit model", "model-compliance"),
    }
    stored = dh_store.data[("project", "credit-scoring", "ai-compliance")]
    assert stored["ai_task"] == "CLASSIFICATION" and stored["domain"] == {"domain": "finance"}
    assert stored["goal"] == PROJECT["goal"] and "name" not in stored  # the name is the DH identifier
    assert stored["context"]["risk_classification"]["risk_level"] == project_context()["risk_classification"]["risk_level"]
    assert all(null_paths(spec) == [] for spec in dh_store.data.values())  # DH schemas reject nulls


def test_get_returns_the_stored_specification_and_loads_it_into_the_session(dh_store):
    save_compliance_specification("project", "p1", ctx(**project_state("p1")))
    save_compliance_specification("dataset", "d1", ctx(**{DATASETS_KEY: {"d1": dataset_spec()}}))
    save_compliance_specification("model", "m1", ctx(**{MODELS_KEY: {"m1": model_spec()}}))

    fresh = ctx()
    project = get_compliance_specification("project", "p1", fresh)
    dataset = get_compliance_specification("dataset", "d1", fresh)
    model = get_compliance_specification("model", "m1", fresh)

    risk_level = project_context()["risk_classification"]["risk_level"]
    assert project["specification"]["context"]["risk_classification"]["risk_level"] == risk_level
    assert dataset["specification"]["scope"] == dataset_spec()["scope"]
    assert model["specification"]["objectives"]
    assert fresh.state[CONTEXT_KEY]["risk_classification"]["risk_level"] == risk_level
    assert fresh.state[PROJECT_KEY]["name"] == "p1" and fresh.state[PROJECT_KEY]["goal"] == PROJECT["goal"]
    assert fresh.state[PROJECT_KEY]["geography"] == project_context()["geography"]  # restored from the context
    assert set(fresh.state[DATASETS_KEY]) == {"d1"} and set(fresh.state[MODELS_KEY]) == {"m1"}


def test_save_accepts_an_explicit_specification_as_object_or_json_text(dh_store):
    first, second = ctx(), ctx()

    as_object = save_compliance_specification("model", "m1", first, specification=model_spec())
    as_text = save_compliance_specification("model", "m2", second, specification=json.dumps(model_spec()))

    assert as_object["source"] == as_text["source"] == "argument"
    assert {k[1] for k in dh_store.data} == {"m1", "m2"}
    assert "m1" in first.state[MODELS_KEY]  # an explicit specification becomes the session's one


def test_save_without_an_analysis_reports_not_found_and_writes_nothing(dh_store):
    out = save_compliance_specification("dataset", "unknown", ctx(**{DATASETS_KEY: {"other": dataset_spec()}}))
    assert out["code"] == "not_found"
    assert dh_store.data == {} and dh_store.calls == []


def test_save_rejects_an_invalid_specification_and_writes_nothing(dh_store):
    broken = project_spec()
    del broken["context"]["risk_classification"]

    out = save_compliance_specification("project", "p1", ctx(), specification=broken)

    assert out["code"] == "invalid_specification" and "risk_classification" in out["error"]
    assert dh_store.data == {}


def test_get_reports_missing_and_invalid_stored_specifications(dh_store):
    assert get_compliance_specification("project", "none", ctx())["code"] == "not_found"

    dh_store.data[("dataset", "d1", "data-compliance")] = {"scope": "NOT-A-SCOPE"}
    fresh = ctx()
    out = get_compliance_specification("dataset", "d1", fresh)

    assert out["code"] == "invalid_specification"
    assert fresh.state == {}  # nothing invalid reaches the session


def test_save_keeps_the_fields_managed_on_the_platform(dh_store):
    dh_store.data[("project", "p1", "ai-compliance")] = {
        **project_spec(),
        "goal": "Old goal",
        "compliance_status": {"status": "IN_REVIEW"},
    }

    save_compliance_specification("project", "p1", ctx(**project_state("p1")))

    stored = dh_store.data[("project", "p1", "ai-compliance")]
    assert stored["goal"] == PROJECT["goal"]  # replaced by the analysis
    assert stored["compliance_status"] == {"status": "IN_REVIEW"}  # kept


def test_get_ignores_the_fields_managed_on_the_platform(dh_store):
    stored = project_spec()
    stored["compliance_status"] = {"status": "IN_REVIEW"}
    stored["context"]["risk_classification"]["assessor"] = {"name": "Reviewer"}
    dh_store.data[("project", "p1", "ai-compliance")] = stored
    dh_store.data[("dataset", "d1", "data-compliance")] = {**dataset_spec(), "governance": {"owner": "x"}}
    fresh = ctx()

    project = get_compliance_specification("project", "p1", fresh)
    dataset = get_compliance_specification("dataset", "d1", fresh)

    assert "compliance_status" not in project["specification"]
    assert "assessor" not in project["specification"]["context"]["risk_classification"]
    assert "governance" not in dataset["specification"]
    assert ComplianceContextOut.model_validate(fresh.state[CONTEXT_KEY])


def test_project_description_without_context_does_not_count_as_an_analysis(dh_store):
    from compliance_adk.agents import coordinator_tools

    description = {k: v for k, v in project_spec().items() if k != "context"}
    dh_store.data[("project", "p1", "ai-compliance")] = description

    assert coordinator_tools._stored_on_dh("project", "p1", ctx()) is None


def test_unknown_kind_is_rejected(dh_store):
    assert get_compliance_specification("service", "x", ctx())["code"] == "invalid_kind"
    assert save_compliance_specification("service", "x", ctx())["code"] == "invalid_kind"
    assert dh_store.calls == []


def test_platform_failures_are_returned_as_dh_errors(dh_store, monkeypatch):
    def unreachable(*args):
        raise ConnectionError("unreachable")

    monkeypatch.setattr(dh, "get_entity_extension", unreachable)
    monkeypatch.setattr(dh, "save_project_extension", unreachable)
    fresh = ctx(**project_state())

    read = get_compliance_specification("dataset", "d1", fresh)
    saved = save_compliance_specification("project", "p1", fresh)

    assert read["code"] == saved["code"] == "dh_error" and "unreachable" in read["error"]
    assert DATASETS_KEY not in fresh.state


def test_tool_declarations_build_for_typed_params():
    for fn in SPECIFICATION_TOOL_REGISTRY.values():
        declaration = FunctionTool(fn)._get_declaration()
        schema = str(declaration.parameters_json_schema or declaration.parameters)
        assert "tool_context" not in schema
        assert all(kind in schema for kind in ("project", "dataset", "model"))


def test_coordinator_saves_and_retrieves_specifications_end_to_end(make_registry, settings, dh_store):
    make_registry(example("project-context"))
    coordinator_llm = ScriptedLlm(
        script=[
            {"call": "load_skill", "args": {"skill_name": "compliance-specifications"}},
            {"call": "analyze_project_context", "args": {"project": PROJECT}},
            {"call": "save_compliance_specification", "args": {"kind": "project", "entity": "credit-scoring"}},
            {"call": "get_compliance_specification", "args": {"kind": "project", "entity": "credit-scoring"}},
            "Saved and retrieved.",
        ],
        seen_messages=[],
    )
    agent = build_coordinator_agent(settings, model=coordinator_llm)

    async def chat():
        sessions = InMemorySessionService()
        runner = Runner(agent=agent, app_name="t", session_service=sessions)
        session = await sessions.create_session(app_name="t", user_id="u")
        message = types.Content(role="user", parts=[types.Part(text="Analyse and store my project")])
        events = [e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=message)]
        return events

    events = asyncio.run(chat())

    assert events[-1].content.parts[0].text == "Saved and retrieved."
    results = {
        part.function_response.name: part.function_response.response
        for e in events
        if e.content
        for part in e.content.parts
        if part.function_response
    }
    assert results["save_compliance_specification"]["saved"] is True
    assert results["get_compliance_specification"]["specification"]["context"]["risk_classification"]["risk_level"] == "HIGH"
    assert ("project", "credit-scoring", "ai-compliance") in dh_store.data


STORED_KEY = ("project", "credit-scoring", "ai-compliance")
GET_PROJECT = {"call": "get_compliance_specification", "args": {"kind": "project", "entity": "credit-scoring"}}
SAVE_PROJECT = {"call": "save_compliance_specification", "args": {"kind": "project", "entity": "credit-scoring"}}
LOAD_SKILL = {"call": "load_skill", "args": {"skill_name": "compliance-specifications"}}
NAMED_PROJECT = {**PROJECT, "name": "credit-scoring"}  # the project name is the DH identifier
ANALYSE = {"call": "analyze_project_context", "args": {"project": NAMED_PROJECT}}
RERUN = {"call": "analyze_project_context", "args": {"project": NAMED_PROJECT, "rerun": True}}


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


def called(events) -> list[str]:
    return [p.function_call.name for e in events if e.content for p in e.content.parts if p.function_call]


def responded(events) -> dict:
    return {
        p.function_response.name: p.function_response.response
        for e in events
        if e.content
        for p in e.content.parts
        if p.function_response
    }


def test_stored_specification_is_presented_without_running_the_analysis(make_registry, settings, dh_store):
    dh_store.data[STORED_KEY] = project_spec()
    _, analysis_llm = make_registry()  # no script: any analysis would fail
    agent = build_coordinator_agent(
        settings, model=ScriptedLlm(script=[ANALYSE, "It is stored; re-run?"], seen_messages=[])
    )

    (turn,), session = run_turns(agent, "Analyse the credit-scoring project")

    out = responded(turn)["analyze_project_context"]
    assert out["stored_on_dh"] is True and out["analysis_run"] is False
    assert out["specification"]["context"]["risk_classification"]["risk_level"] == "HIGH"
    assert "re-run" in out["message"] and "rerun=True" in out["message"]
    assert analysis_llm.seen_messages == []
    assert session.state[CONTEXT_KEY]["risk_classification"]["risk_level"] == "HIGH"  # loaded for reuse
    assert dh_store.data[STORED_KEY] == project_spec()  # nothing was overwritten


def test_user_can_re_run_a_stored_analysis_and_replace_it(make_registry, settings, dh_store):
    dh_store.data[STORED_KEY] = project_spec()
    rerun = example("project-context")
    rerun["result"]["risk_classification"]["rationale"] = "Re-run rationale."
    _, analysis_llm = make_registry(rerun)
    agent = build_coordinator_agent(
        settings,
        model=ScriptedLlm(
            script=[ANALYSE, "It is stored; re-run?", RERUN, LOAD_SKILL, SAVE_PROJECT, "Re-run saved."],
            seen_messages=[],
        ),
    )

    (first, second), _ = run_turns(agent, "Analyse the credit-scoring project", "Yes, re-run it and save")

    assert responded(first)["analyze_project_context"]["analysis_run"] is False
    assert "data" in responded(second)["analyze_project_context"]  # the analysis ran this time
    assert len(analysis_llm.seen_messages) == 1
    assert dh_store.data[STORED_KEY]["context"]["risk_classification"]["rationale"] == "Re-run rationale."


def test_missing_specification_is_analysed_then_saved(make_registry, settings, dh_store):
    _, analysis_llm = make_registry(example("project-context"))
    agent = build_coordinator_agent(
        settings, model=ScriptedLlm(script=[ANALYSE, LOAD_SKILL, SAVE_PROJECT, "Analysed and saved."], seen_messages=[])
    )

    (turn,), _ = run_turns(agent, "Analyse the credit-scoring project")

    assert "data" in responded(turn)["analyze_project_context"]
    assert "stored_on_dh" not in responded(turn)["analyze_project_context"]
    assert len(analysis_llm.seen_messages) == 1
    assert STORED_KEY in dh_store.data


@pytest.mark.parametrize(
    "tool_name, kind, entity, extension_kind, spec",
    [
        ("analyze_dataset", "dataset", "Applications 2024", "data-compliance", dataset_spec),
        ("analyze_model", "model", "Credit model", "model-compliance", model_spec),
    ],
)
def test_dataset_and_model_analyses_check_dh_first(dh_store, tool_name, kind, entity, extension_kind, spec):
    from compliance_adk.agents import coordinator_tools

    from .conftest import DATASET, MODEL

    dh_store.data[(kind, entity, extension_kind)] = spec()
    tool_context = ctx()

    out = asyncio.run(getattr(coordinator_tools, tool_name)({"dataset": DATASET, "model": MODEL}[kind], tool_context))

    assert out["stored_on_dh"] is True and out["analysis_run"] is False and out["kind"] == kind
    assert ("get_entity", entity, kind, extension_kind) in dh_store.calls
    assert tool_context.state  # the stored specification was loaded into the session


def test_retrieved_project_context_is_reused_by_a_later_dataset_analysis(make_registry, settings, dh_store):
    dh_store.data[STORED_KEY] = project_spec()
    _, analysis_llm = make_registry(example("dataset-analysis"))
    dataset = {"name": "Applications 2024", "scope": "TRAINING"}
    agent = build_coordinator_agent(
        settings,
        model=ScriptedLlm(
            script=[LOAD_SKILL, GET_PROJECT, {"call": "analyze_dataset", "args": {"dataset": dataset}}, "Done."],
            seen_messages=[],
        ),
    )

    run_turns(agent, "Analyse the dataset of the credit-scoring project")

    assert len(analysis_llm.seen_messages) == 1 and '"project_context"' in analysis_llm.seen_messages[0]


def test_guidance_tells_the_agent_about_the_check_and_rerun_decision():
    from compliance_adk.agents.coordinator import INSTRUCTION
    from compliance_adk.skill_loader import load_skill

    skill = load_skill("compliance-specifications").instructions
    assert "stored_on_dh" in skill and "rerun=True" in skill and "not_found" in skill
    assert "stored_on_dh" in INSTRUCTION and "rerun=True" in INSTRUCTION and "re-run the analysis" in INSTRUCTION
