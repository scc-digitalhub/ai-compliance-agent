# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Opt-in live-provider scenarios. Run from adk/ with:

    python -m pytest manual_tests/test_real_model_scenarios.py -q -s

These checks use model roles and credentials loaded from adk/.env and are not part of
normal pytest discovery (which is restricted to tests/ in pyproject.toml).
"""
from __future__ import annotations

import asyncio
import json

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_core.state import CONTEXT_KEY, DATASETS_KEY, MODELS_KEY
from compliance_adk.config import Settings
from compliance_core.contracts import (
    ComplianceContextOut,
    DatasetAnalysisRequest,
    DatasetInput,
    ModelAnalysisRequest,
    ModelInput,
    ProjectComplianceSpec,
    ProjectInput,
)
from compliance_dh import tools as dh
from compliance_adk.runtime import RunnerRegistry, set_registry

PROJECT = ProjectInput(
    name="Credit scoring",
    domain="finance",
    ai_task="CLASSIFICATION",
    goal="Estimate creditworthiness for loan applications while supporting human review.",
    purpose="Help loan officers prioritize applications for review; do not make final decisions automatically.",
    audience="Loan officers and applicants",
    geography=["EU"],
    environment="PILOT",
)
DATASET = DatasetInput(
    name="Loan applications pilot",
    description="Synthetic application records for evaluating a creditworthiness model.",
    scope="TRAINING",
    domain="finance",
    sensitivity="PII",
    n_records=50000,
    schema_fields=[
        {"name": "age", "dtype": "integer", "sensitivity": "quasi-identifier"},
        {"name": "annual_income", "dtype": "number"},
        {"name": "employment_years", "dtype": "number"},
        {"name": "repayment_history", "dtype": "category"},
        {"name": "approved", "dtype": "boolean"},
    ],
    sample_records=[
        {"age": 42, "annual_income": 62000, "employment_years": 8, "repayment_history": "good", "approved": True},
        {"age": 29, "annual_income": 38000, "employment_years": 3, "repayment_history": "limited", "approved": False},
    ],
    known_protected_attributes=["age", "sex"],
)
MODEL = ModelInput(
    name="Creditworthiness classifier",
    ai_task="CLASSIFICATION",
    domain="finance",
    framework="SKLEARN",
    output_type="BINARY_CLASSIFICATION",
    produces_probabilities=True,
    trained_on_sensitive_data=True,
    known_affected_groups=["older applicants", "applicants with limited credit history"],
)


def _settings() -> Settings:
    settings = Settings()
    for role in ("project_context", "dataset", "model", "coordinator"):
        settings.model_name_for(role)
    return settings


def test_structured_agents_real_model_chain():
    settings = _settings()

    async def run_chain():
        registry = RunnerRegistry(settings)
        project_result = await registry.get("project_context").run(PROJECT)
        assert project_result.data.risk_classification.risk_level
        assert project_result.data.requirements

        dataset_result = await registry.get("dataset").run(
            DatasetAnalysisRequest(
                dataset=DATASET,
                project=PROJECT,
                project_context=project_result.data,
            )
        )
        assert dataset_result.data.scope == DATASET.scope
        assert dataset_result.data.objectives

        model_result = await registry.get("model").run(
            ModelAnalysisRequest(
                model=MODEL,
                project=PROJECT,
                project_context=project_result.data,
                dataset_compliance=[dataset_result.data],
            )
        )
        assert model_result.data.objectives

    asyncio.run(run_chain())


def test_coordinator_real_model_runs_and_reuses_analysis_results():
    settings = _settings()

    async def run_conversation():
        registry = RunnerRegistry(settings)
        set_registry(registry)
        sessions = InMemorySessionService()
        runner = Runner(
            agent=build_coordinator_agent(settings),
            app_name="real_model_manual_check",
            session_service=sessions,
        )
        session = await sessions.create_session(app_name="real_model_manual_check", user_id="manual-check")
        prompt = (
            "Run all three analyses now, using the coordinator tools in this order: project context, "
            "dataset, then model. Use the returned context automatically for the later analyses and "
            "do not invent results. Project: "
            f"{PROJECT.model_dump_json()} Dataset: {DATASET.model_dump_json()} Model: {MODEL.model_dump_json()} "
            "Afterward, briefly summarize the risk and the key dataset and model compliance findings."
        )
        try:
            events = [
                event
                async for event in runner.run_async(
                    user_id="manual-check",
                    session_id=session.id,
                    new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
                )
            ]
            updated = await sessions.get_session(
                app_name="real_model_manual_check", user_id="manual-check", session_id=session.id
            )
            assert updated is not None
            assert "analysis_project_context" in updated.state
            assert updated.state.get("analysis_datasets")
            assert updated.state.get("analysis_models")
            final_text = "\n".join(
                part.text or ""
                for event in events
                if event.is_final_response() and event.content
                for part in event.content.parts
            )
            assert final_text.strip(), "Coordinator produced no final response"
            print("Coordinator summary:", final_text)
        finally:
            set_registry(None)

    asyncio.run(run_conversation())


def _example_result(skill: str) -> dict:
    path = _settings().skills_path / skill / "references" / "example.json"
    return json.loads(path.read_text())["result"]


@pytest.fixture
def dh_store(monkeypatch):
    """In-memory stand-in for the DH platform; keys are (entity kind, entity, extension kind)."""
    store: dict[tuple[str, str, str], dict] = {}
    monkeypatch.setattr(dh, "get_project_extension", lambda project, extension_kind: store.get(("project", project, extension_kind), {}))
    monkeypatch.setattr(dh, "get_entity_extension", lambda entity, entity_kind, extension_kind: store.get((entity_kind, entity, extension_kind), {}))
    monkeypatch.setattr(dh, "save_project_extension", lambda project, extension_kind, extension: store.__setitem__(("project", project, extension_kind), extension))
    monkeypatch.setattr(dh, "save_entity_extension", lambda entity, entity_kind, extension_kind, extension: store.__setitem__((entity_kind, entity, extension_kind), extension))
    return store


async def _converse(runner, session_id: str, prompt: str) -> tuple[list[str], str]:
    """One user turn; returns the names of the tools the model called and its final text."""
    events = [
        event
        async for event in runner.run_async(
            user_id="manual-check",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        )
    ]
    calls = [p.function_call.name for e in events if e.content for p in e.content.parts if p.function_call]
    text = "\n".join(
        part.text or ""
        for event in events
        if event.is_final_response() and event.content
        for part in event.content.parts
    )
    return calls, text


def test_coordinator_real_model_saves_and_retrieves_specifications(dh_store):
    """Session A stores three specifications; a new session B retrieves one from the DH store.

    An in-memory store stands in for the DH platform (see test_dh_platform_scenarios.py for the real one).
    """
    settings = _settings()
    store = dh_store

    async def converse(sessions, runner, session_id: str, prompt: str) -> str:
        return (await _converse(runner, session_id, prompt))[1]

    async def run_scenario():
        set_registry(RunnerRegistry(settings))
        sessions = InMemorySessionService()
        runner = Runner(
            agent=build_coordinator_agent(settings),
            app_name="real_model_manual_check",
            session_service=sessions,
        )
        try:
            seeded = await sessions.create_session(
                app_name="real_model_manual_check",
                user_id="manual-check",
                state={
                    CONTEXT_KEY: _example_result("project-context"),
                    DATASETS_KEY: {DATASET.name: _example_result("dataset-analysis")},
                    MODELS_KEY: {MODEL.name: _example_result("model-analysis")},
                },
            )
            saved_reply = await converse(
                sessions,
                runner,
                seeded.id,
                "Store the analysed compliance specifications on the DH platform: the project "
                f"'credit-scoring', the dataset '{DATASET.name}' and the model '{MODEL.name}'. "
                "Use the specifications already analysed in this conversation.",
            )
            print("Save reply:", saved_reply)
            assert set(store) == {
                ("project", "credit-scoring", "ai-compliance"),
                ("dataset", DATASET.name, "data-compliance"),
                ("model", MODEL.name, "model-compliance"),
            }

            fresh = await sessions.create_session(app_name="real_model_manual_check", user_id="manual-check")
            retrieved_reply = await converse(
                sessions,
                runner,
                fresh.id,
                "Retrieve the stored compliance specification of project 'credit-scoring' from the DH "
                "platform and tell me its risk level and classification status.",
            )
            print("Retrieve reply:", retrieved_reply)
            updated = await sessions.get_session(
                app_name="real_model_manual_check", user_id="manual-check", session_id=fresh.id
            )
            assert updated.state[CONTEXT_KEY]["risk_classification"]["risk_level"] == "HIGH"
            assert "high" in retrieved_reply.lower()
        finally:
            set_registry(None)

    asyncio.run(run_scenario())


@pytest.fixture
def analysis_runs(monkeypatch):
    """Records every structured analysis the coordinator triggers (the real analysis is still executed)."""
    from compliance_adk.runtime.runner import StructuredRunner

    runs: list[str] = []
    original = StructuredRunner.run

    async def recording_run(self, request, request_id=None):
        runs.append(self.spec.key if hasattr(self.spec, "key") else type(request).__name__)
        return await original(self, request, request_id)

    monkeypatch.setattr(StructuredRunner, "run", recording_run)
    return runs


ANALYSE_PROMPT = (
    "Analyse my project 'credit-scoring': a finance credit scoring classification system in a pilot "
    "environment for EU loan officers and applicants. Goal: estimate creditworthiness for loan applications "
    "while supporting human review. Purpose: help officers prioritise applications; no automatic final decisions."
)


def _coordinator_session(settings):
    async def create():
        set_registry(RunnerRegistry(settings))
        sessions = InMemorySessionService()
        runner = Runner(agent=build_coordinator_agent(settings), app_name="check_first", session_service=sessions)
        session = await sessions.create_session(app_name="check_first", user_id="manual-check")
        return sessions, runner, session

    return create


def test_coordinator_real_model_presents_stored_specification_instead_of_analysing(dh_store, analysis_runs):
    """A specification already on DH is retrieved and offered; no analysis runs until the user decides."""
    settings = _settings()
    context = ComplianceContextOut.model_validate(_example_result("project-context"))
    stored = ProjectComplianceSpec.of(PROJECT.model_copy(update={"name": "credit-scoring"}), context)
    dh_store[("project", "credit-scoring", "ai-compliance")] = stored.model_dump(mode="json", exclude_none=True)

    async def scenario():
        sessions, runner, session = await _coordinator_session(settings)()
        try:
            calls, reply = await _converse(runner, session.id, ANALYSE_PROMPT)
            print("Tools:", calls, "\nReply:", reply)
            updated = await sessions.get_session(app_name="check_first", user_id="manual-check", session_id=session.id)
            assert "get_compliance_specification" in calls or "analyze_project_context" in calls
            assert analysis_runs == []  # the stored specification was presented, not re-analysed
            assert updated.state[CONTEXT_KEY]["risk_classification"]["risk_level"] == "HIGH"
            assert any(word in reply.lower() for word in ("re-run", "rerun", "again", "re-analy", "reanaly"))
        finally:
            set_registry(None)

    asyncio.run(scenario())


def test_coordinator_real_model_analyses_when_specification_is_missing(dh_store, analysis_runs):
    """Nothing on DH: the coordinator checks, finds nothing and performs the analysis (real structured agent)."""
    settings = _settings()

    async def scenario():
        sessions, runner, session = await _coordinator_session(settings)()
        try:
            calls, reply = await _converse(runner, session.id, ANALYSE_PROMPT)
            print("Tools:", calls, "\nReply:", reply)
            updated = await sessions.get_session(app_name="check_first", user_id="manual-check", session_id=session.id)
            assert "analyze_project_context" in calls
            assert len(analysis_runs) == 1
            assert CONTEXT_KEY in updated.state
        finally:
            set_registry(None)

    asyncio.run(scenario())
