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
from compliance_core.knowledge import get_bundle

from compliance_api.app import create_app
from compliance_api.config import ApiSettings
from compliance_api.engine import LiteLlmEngine
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
