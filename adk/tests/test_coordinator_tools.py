from __future__ import annotations

import asyncio
from types import SimpleNamespace

from google.adk.tools import FunctionTool

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.agents.coordinator_tools import (
    COORDINATOR_TOOLS,
    analyze_dataset,
    analyze_model,
    analyze_project_context,
    get_session_analyses,
)
from compliance_adk.contracts import DatasetInput, ModelInput, ProjectInput

from .conftest import DATASET, MODEL, PROJECT, ScriptedLlm, example


def ctx() -> SimpleNamespace:
    return SimpleNamespace(state={})


def test_results_are_stored_and_reused_by_later_analyses(make_registry):
    _, llm = make_registry(example("project-context"), example("dataset-analysis"), example("model-analysis"))
    tool_context = ctx()

    async def flow():
        project = await analyze_project_context(ProjectInput(**PROJECT), tool_context)
        dataset = await analyze_dataset(DatasetInput(**DATASET), tool_context)
        model = await analyze_model(ModelInput(**MODEL), tool_context)
        return project, dataset, model

    project, dataset, model = asyncio.run(flow())

    assert project["data"]["risk_classification"]["risk_level"] == "HIGH" and project["grounding"] == []
    # dataset and model requests carry the stored project and its context
    assert '"project_context"' in llm.seen_messages[1] and '"project"' in llm.seen_messages[1]
    assert '"dataset_compliance"' in llm.seen_messages[2]
    stored = get_session_analyses(tool_context)
    assert stored["project"]["name"] == "Credit scoring"
    assert set(stored["datasets"]) == {DATASET["name"]} and set(stored["models"]) == {MODEL["name"]}


def test_tool_errors_are_returned_not_raised(make_registry):
    _, llm = make_registry()
    llm.fail_with = RuntimeError("boom")
    out = asyncio.run(analyze_project_context(ProjectInput(**PROJECT), ctx()))
    assert out["code"] == "upstream_model_error"


def test_tool_declarations_build_for_typed_params():
    names = {}
    for fn in COORDINATOR_TOOLS:
        declaration = FunctionTool(fn)._get_declaration()
        names[declaration.name] = declaration
    assert set(names) == {"analyze_project_context", "analyze_dataset", "analyze_model", "get_session_analyses"}
    assert "tool_context" not in str(names["analyze_dataset"].parameters_json_schema or names["analyze_dataset"].parameters)


def test_coordinator_agent_is_built(settings):
    agent = build_coordinator_agent(settings, model=ScriptedLlm())
    assert agent.name == "compliance_agent"
    assert len(agent.tools) == 5  # skill toolset + four function tools


def test_coordinator_runs_analysis_end_to_end(make_registry, settings):
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    make_registry(example("project-context"))
    coordinator_llm = ScriptedLlm(
        script=[
            {"call": "analyze_project_context", "args": {"project": PROJECT}},
            "The project is high risk.",
        ],
        seen_messages=[],
    )
    agent = build_coordinator_agent(settings, model=coordinator_llm)

    async def chat():
        sessions = InMemorySessionService()
        runner = Runner(agent=agent, app_name="t", session_service=sessions)
        session = await sessions.create_session(app_name="t", user_id="u")
        message = types.Content(role="user", parts=[types.Part(text="Analyse my credit scoring project")])
        events = [e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=message)]
        return events, await sessions.get_session(app_name="t", user_id="u", session_id=session.id)

    events, session = asyncio.run(chat())

    assert events[-1].content.parts[0].text == "The project is high risk."
    assert session.state["analysis_project"]["name"] == "Credit scoring"
    assert session.state["analysis_project_context"]["risk_classification"]["risk_level"] == "HIGH"


def test_structured_agent_works_with_models_lacking_native_schema_and_tools(settings):
    from compliance_adk.contracts import ProjectInput
    from compliance_adk.runtime import RunnerRegistry
    from google.adk.models._capabilities import LlmCapabilities

    class NoNativeSchemaLlm(ScriptedLlm):
        @property
        def capabilities(self) -> LlmCapabilities:
            return LlmCapabilities(output_schema_and_tools=False)

    llm = NoNativeSchemaLlm(
        script=[{"call": "set_model_response", "args": example("project-context")}], seen_messages=[]
    )
    registry = RunnerRegistry(settings, model=llm)
    out = asyncio.run(registry.get("project_context").run(ProjectInput(**PROJECT)))
    assert out.data.risk_classification.risk_level == "HIGH"
