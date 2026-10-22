"""Opt-in live-provider scenarios. Run from adk/ with:

    python -m pytest manual_tests/test_real_model_scenarios.py -q -s

These checks use model roles and credentials loaded from adk/.env and are not part of
normal pytest discovery (which is restricted to tests/ in pyproject.toml).
"""
from __future__ import annotations

import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.config import Settings
from compliance_adk.contracts import (
    DatasetAnalysisRequest,
    DatasetInput,
    ModelAnalysisRequest,
    ModelInput,
    ProjectInput,
)
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
