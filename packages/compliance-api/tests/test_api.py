# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from compliance_core.contracts import AnalysisMeta, AnalysisResponse
from compliance_core.contracts.evaluation_code import (
    MetricEvaluationCodeArtifact,
    MetricEvaluationCodeOutput,
    MetricEvaluationCodeRequest,
)
from compliance_core.knowledge import get_bundle
from compliance_core.contracts.report_code import ReportCodeArtifact, ReportCodeOutput, ReportCodeRequest

from compliance_api.app import create_app
from compliance_api.config import ApiSettings
from compliance_api.engine import AnalysisRegistry, LiteLlmEngine
from compliance_api.specs import ALL_SPECS, PROJECT_CONTEXT


SKILLS = files("compliance_skills").joinpath("skills")


def _example(name: str) -> dict:
    return json.loads(SKILLS.joinpath(name, "references", "example.json").read_text())


class _FakeEngine:
    def __init__(self, key: str):
        self.key = key

    async def run(self, analysis, request, request_id=None):
        skill_name = {
            "project_context": "project-context",
            "dataset": "dataset-analysis",
            "model": "model-analysis",
        }[analysis]
        spec = {spec.key: spec for spec in ALL_SPECS}[analysis]
        output = spec.output_model.model_validate(_example(skill_name))
        return AnalysisResponse[type(output.result)](
            data=output.result,
            meta=AnalysisMeta(
                request_id=request_id or "test",
                agent=spec.agent_name,
                model="fake",
                okf_version=get_bundle().version,
                latency_ms=1,
                attempts=1,
                assumptions=output.assumptions,
            ),
        )


class _Registry:
    bundle = get_bundle()

    def get(self, key: str):
        return _FakeEngine(key)


@pytest.fixture
def client():
    with TestClient(create_app(ApiSettings(), _Registry())) as test_client:
        yield test_client


def test_context_endpoint_returns_typed_envelope(client):
    result = client.post(
        "/v1/compliance/context",
        json={
            "name": "Credit scoring",
            "domain": "finance",
            "ai_task": "CLASSIFICATION",
            "goal": "Assess creditworthiness",
        },
        headers={"X-Request-ID": "req-1"},
    )
    assert result.status_code == 200
    assert result.json()["meta"]["request_id"] == "req-1"
    assert result.json()["meta"]["agent"] == "project_context_agent"
    assert result.headers["X-Request-ID"] == "req-1"


def test_dataset_and_model_endpoints_return_expected_types(client):
    dataset = client.post(
        "/v1/compliance/datasets",
        json={"dataset": {"name": "Applications", "scope": "TRAINING"}},
    )
    model = client.post(
        "/v1/compliance/models",
        json={"model": {"name": "Credit model", "ai_task": "CLASSIFICATION"}},
    )
    assert dataset.status_code == 200
    assert dataset.json()["data"]["scope"] == "TRAINING"
    assert model.status_code == 200
    assert model.json()["data"]["objectives"]


def test_invalid_input_and_api_key_are_enforced():
    settings = ApiSettings(api_keys="secret")
    with TestClient(create_app(settings, _Registry())) as client:
        assert client.post("/v1/compliance/context", json={"name": "x"}).status_code == 401
        invalid = client.post(
            "/v1/compliance/context",
            json={"name": "x"},
            headers={"X-API-Key": "secret"},
        )
    assert invalid.status_code == 422


def test_litellm_engine_runs_without_adk_and_validates_output():
    expected = _example("project-context")

    async def completion(**kwargs):
        assert kwargs["tools"]
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(expected),
                        tool_calls=None,
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=7, completion_tokens=5),
        )

    settings = ApiSettings(structured_model="scripted")
    engine = LiteLlmEngine(PROJECT_CONTEXT, settings, completion=completion)
    request = PROJECT_CONTEXT.request_model.model_validate(
        {
            "name": "Credit scoring",
            "domain": "finance",
            "ai_task": "CLASSIFICATION",
            "goal": "Assess creditworthiness",
        }
    )
    response = asyncio.run(engine.run("project_context", request, "api-test"))
    assert response.meta.request_id == "api-test"
    assert response.meta.usage.input_tokens == 7
    assert response.data.risk_classification.risk_level == "HIGH"


def test_litellm_engine_executes_allowed_core_tools():
    expected = _example("project-context")
    calls = 0

    async def completion(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=None,
                            tool_calls=[
                                {
                                    "id": "tool-1",
                                    "type": "function",
                                    "function": {
                                        "name": "get_regulatory_refs",
                                        "arguments": '{"frameworks":"eu-ai-act"}',
                                    },
                                }
                            ],
                        )
                    )
                ],
                usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2),
            )
        assert kwargs["messages"][-1]["role"] == "tool"
        assert kwargs["messages"][-1]["name"] == "get_regulatory_refs"
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(expected),
                        tool_calls=None,
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=4),
        )

    settings = ApiSettings(structured_model="scripted")
    engine = LiteLlmEngine(PROJECT_CONTEXT, settings, completion=completion)
    request = PROJECT_CONTEXT.request_model.model_validate(
        {
            "name": "Credit scoring",
            "domain": "finance",
            "ai_task": "CLASSIFICATION",
            "goal": "Assess creditworthiness",
        }
    )
    response = asyncio.run(engine.run("project_context", request, "tool-test"))
    assert calls == 2
    assert response.meta.usage.input_tokens == 8
    assert response.meta.grounding


def test_api_imports_without_google_adk():
    root = Path(__file__).resolve().parents[3]
    packages = root / "packages"
    package_sources = [
        packages / "compliance-core" / "src",
        packages / "compliance-dh" / "src",
        packages / "compliance-skills" / "src",
        packages / "compliance-api" / "src",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(map(str, package_sources))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from importlib.abc import MetaPathFinder

class BlockAdk(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "google.adk" or fullname.startswith("google.adk."):
            raise AssertionError("standalone API imported Google ADK")
        return None

sys.meta_path.insert(0, BlockAdk())
import compliance_api.app
""",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_api_serves_the_core_analysis_definitions():
    from compliance_core.analysis_engine import ANALYSES

    assert ALL_SPECS is ANALYSES


def test_code_generation_model_roles_use_structured_model_fallback():
    from compliance_api.config import ApiSettings

    shared = ApiSettings(structured_model="shared-model")
    assert shared.model_name_for("metric_evaluation_code") == "shared-model"
    assert shared.model_name_for("compliance_report_code") == "shared-model"


class _EvaluationRouteRegistry:
    bundle = get_bundle()

    def get(self, key: str):
        return _EvaluationRouteEngine(key)


class _EvaluationRouteEngine:
    def __init__(self, key: str):
        self.key = key

    async def run(self, operation, request, request_id=None):
        assert operation == self.key
        if self.key == "metric_evaluation_code":
            assert isinstance(request, MetricEvaluationCodeRequest)
            data = MetricEvaluationCodeOutput(
                result=MetricEvaluationCodeArtifact(
                    status="needs_input", missing_inputs=["explicit data binding"],
                )
            ).result
        else:
            assert self.key == "compliance_report_code"
            assert isinstance(request, ReportCodeRequest)
            data = ReportCodeOutput(
                result=ReportCodeArtifact(
                    status="needs_input",
                    language=request.language,
                    mode=request.mode,
                    missing_inputs=["result source"],
                )
            ).result
        return AnalysisResponse[type(data)](
            data=data,
            meta=AnalysisMeta(
                request_id=request_id or "test",
                agent=f"{self.key}_agent",
                model="fake",
                okf_version=get_bundle().version,
                latency_ms=1,
                attempts=1,
                assumptions=["test assumption"],
            ),
        )


def _error_envelope() -> dict:
    return {
        "project": "credit",
        "entity": "model-1",
        "objective_ref": "obj-1",
        "objective": {
            "name": "Accuracy threshold",
            "description": "Check the declared accuracy result",
            "metric": {"id": "metric-accuracy", "name": "Accuracy", "kind": "PRIMITIVE", "scale": "RATIO"},
            "condition": {"threshold": {"operator": "GEQ", "value": 0.8}},
        },
        "status": "ERROR",
        "error": "External evaluator failed",
    }


def test_evaluation_code_routes_use_fake_registry():
    with TestClient(create_app(ApiSettings(), _EvaluationRouteRegistry())) as test_client:
        metric = test_client.post(
            "/v1/compliance/metric-evaluation/code",
            json={
                "project": "credit",
                "entity_kind": "model",
                "entity": "model-1",
                "objective_ref": "obj-1",
                "objective": {
                    "metric": {
                        "id": "metric-accuracy",
                        "name": "Accuracy",
                        "kind": "PRIMITIVE",
                        "scale": "RATIO",
                    },
                    "condition": {"threshold": {"operator": "GEQ", "value": 0.8}},
                },
            },
        )
        report_code = test_client.post(
            "/v1/compliance/reports/code",
            json={
                "project": "credit",
                "entity_kind": "model",
                "entity": "model-1",
                "language": "python",
            },
        )
    assert metric.status_code == 200
    assert metric.json()["data"]["status"] == "needs_input"
    assert metric.json()["meta"]["assumptions"] == ["test assumption"]
    assert report_code.status_code == 200
    assert report_code.json()["data"]["mode"] == "standalone"


def test_report_routes_build_and_validate_inline_results():
    with TestClient(create_app(ApiSettings(), _EvaluationRouteRegistry())) as test_client:
        built = test_client.post(
            "/v1/compliance/reports",
            json={"results": [_error_envelope()], "variants": ["TEST"]},
        )
        assert built.status_code == 200, built.text
        report = built.json()["reports"]["TEST"]
        validated = test_client.post("/v1/compliance/reports/validate", json={"report": report})

    assert validated.status_code == 200
    assert validated.json()["valid"] is True
    assert validated.json()["report"]["kind"] == "TEST"


def test_report_route_requires_injected_reader_for_source_references():
    with TestClient(create_app(ApiSettings(), _EvaluationRouteRegistry())) as test_client:
        response = test_client.post(
            "/v1/compliance/reports",
            json={"source": "results.json", "variants": ["TEST"]},
        )
    assert response.status_code == 422


def test_report_route_uses_only_an_explicitly_injected_reader():
    payload = json.dumps({"results": [_error_envelope()]}).encode()
    app = create_app(
        ApiSettings(),
        _EvaluationRouteRegistry(),
        evaluation_input_reader=lambda source: payload if source == "approved:run-1" else b"",
    )
    with TestClient(app) as test_client:
        response = test_client.post(
            "/v1/compliance/reports",
            json={"source": "approved:run-1", "variants": ["TEST"]},
        )
    assert response.status_code == 200, response.text
    assert response.json()["input_source"]["identity"] == "approved:run-1"


def test_api_registry_registers_code_generation_operations_without_provider_calls():
    registry = AnalysisRegistry(ApiSettings(structured_model="scripted"))
    assert registry.get("metric_evaluation_code").spec.key == "metric_evaluation_code"
    assert registry.get("compliance_report_code").spec.key == "compliance_report_code"


def test_run_evals_cli_compares_models_with_scripted_completions(monkeypatch, tmp_path):
    import importlib.util

    import litellm

    async def completion(**kwargs):
        request = json.loads(next(m["content"] for m in kwargs["messages"] if m["role"] == "user"))
        skill = "dataset-analysis" if "dataset" in request else "model-analysis" if "model" in request else "project-context"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(_example(skill)), tool_calls=None))],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=1),
        )

    monkeypatch.setattr(litellm, "acompletion", completion)
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location("run_evals", root / "scripts" / "run_evals.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out, markdown = tmp_path / "report.json", tmp_path / "report.md"
    monkeypatch.setattr(sys, "argv", [
        "run_evals.py", "--model", "scripted-a", "--model", "scripted-b",
        "--case", "consumer-credit-scoring", "--case", "credit-scoring-model",
        "--out", str(out), "--markdown", str(markdown), "--min-validity", "1",
    ])

    assert module.main() == 0
    reports = json.loads(out.read_text())
    assert [report["label"] for report in reports] == ["scripted-a", "scripted-b"]
    assert reports[0]["summary"]["validity_rate"] == 1.0
    assert reports[0]["summary"]["risk_accuracy"] == 1.0
    assert "| Metric | scripted-a | scripted-b |" in markdown.read_text()


def test_litellm_engine_can_run_without_digitalhub_tools():
    seen = {}

    async def completion(**kwargs):
        seen["tools"] = {tool["function"]["name"] for tool in kwargs["tools"]}
        message = SimpleNamespace(content=json.dumps(_example("project-context")), tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)

    request = PROJECT_CONTEXT.request_model.model_validate(
        {"name": "credit", "domain": "finance", "ai_task": "CLASSIFICATION", "goal": "Score loans"}
    )
    for enable_dh, expected in ((True, True), (False, False)):
        engine = LiteLlmEngine(PROJECT_CONTEXT, ApiSettings(structured_model="s", enable_dh=enable_dh),
                               completion=completion)
        asyncio.run(engine.run("project_context", request))
        assert ("get_compliance_specification" in seen["tools"]) is expected
        assert "get_requirements" in seen["tools"]
