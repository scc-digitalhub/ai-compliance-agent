from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from compliance_adk.api.app import create_app
from compliance_adk.config import Settings

from .conftest import DATASET, MODEL, PROJECT, example


@pytest.fixture
def client_factory(make_registry, settings):
    def _make(*script, **settings_overrides):
        registry, llm = make_registry(*script)
        app = create_app(Settings(**{**settings.model_dump(), **settings_overrides}), registry)
        return TestClient(app), llm

    return _make


def test_context_endpoint_returns_envelope(client_factory):
    with client_factory(example("project-context"))[0] as client:
        res = client.post("/v1/compliance/context", json=PROJECT, headers={"X-Request-ID": "abc-1"})
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["risk_classification"]["risk_level"] == "HIGH"
    assert body["meta"]["request_id"] == "abc-1" and res.headers["X-Request-ID"] == "abc-1"
    assert body["meta"]["agent"] == "project_context_agent"


def test_dataset_and_model_endpoints(client_factory):
    client, llm = client_factory(example("dataset-analysis"), example("model-analysis"))
    with client:
        ds = client.post("/v1/compliance/datasets", json={"dataset": DATASET})
        md = client.post("/v1/compliance/models", json={"model": MODEL})
    assert ds.status_code == 200 and ds.json()["data"]["scope"] == "TRAINING"
    assert md.status_code == 200 and md.json()["data"]["objectives"]


def test_invalid_input_is_422_and_never_reaches_the_model(client_factory):
    client, llm = client_factory()
    with client:
        res = client.post("/v1/compliance/context", json={"name": "x"})
        too_many = client.post(
            "/v1/compliance/datasets",
            json={"dataset": {**DATASET, "sample_records": [{}, {}, {}, {}]}},
        )
    assert res.status_code == 422 and too_many.status_code == 422
    assert llm.seen_messages == []


def test_lowercase_enums_are_accepted(client_factory):
    with client_factory(example("project-context"))[0] as client:
        res = client.post("/v1/compliance/context", json={**PROJECT, "deployment": "edge", "environment": "pilot"})
    assert res.status_code == 200


def test_api_key_is_enforced_when_configured(client_factory):
    client, _ = client_factory(example("project-context"), api_keys="k1,k2")
    with client:
        assert client.post("/v1/compliance/context", json=PROJECT).status_code == 401
        assert client.post("/v1/compliance/context", json=PROJECT, headers={"X-API-Key": "nope"}).status_code == 401
        ok = client.post("/v1/compliance/context", json=PROJECT, headers={"X-API-Key": "k2"})
        assert ok.status_code == 200
        assert client.get("/health").status_code == 200


def test_oversized_body_is_rejected(client_factory):
    client, _ = client_factory(max_body_bytes=50)
    with client:
        res = client.post("/v1/compliance/context", json=PROJECT)
    assert res.status_code == 413 and res.json()["code"] == "payload_too_large"


def test_invalid_model_output_maps_to_502(client_factory):
    bad = example("model-analysis")
    bad["result"]["objectives"][0]["requirements"] = ["req-unknown"]
    client, _ = client_factory(bad, bad)
    with client:
        res = client.post("/v1/compliance/models", json={"model": MODEL})
    assert res.status_code == 502 and res.json()["code"] == "invalid_model_output"
    assert res.json()["request_id"]


def test_provider_failure_maps_to_502(client_factory):
    client, llm = client_factory()
    llm.fail_with = RuntimeError("boom")
    with client:
        res = client.post("/v1/compliance/context", json=PROJECT)
    assert res.status_code == 502 and res.json()["code"] == "upstream_model_error"


def test_health_and_ready(client_factory):
    with client_factory()[0] as client:
        assert client.get("/health").json() == {"status": "ok"}
        ready = client.get("/ready")
    assert ready.status_code == 200 and ready.json()["concepts"] > 100


def test_openapi_exposes_typed_schemas(client_factory):
    with client_factory()[0] as client:
        spec = client.get("/openapi.json").json()
    assert set(spec["paths"]) >= {"/v1/compliance/context", "/v1/compliance/datasets", "/v1/compliance/models"}
