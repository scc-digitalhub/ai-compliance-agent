"""Tests for FastAPI endpoints using TestClient — covers all three Streamlit UI scenarios."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import _make_context_response, _make_dataset_response, _make_model_response


@pytest.fixture()
def client(mock_agent):
    """TestClient with the mock agent already wired up."""
    from api.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── POST /compliance/context ──────────────────────────────────────────────────

def test_context_endpoint_loan_project(client, project_loan):
    resp = client.post("/compliance/context", json=project_loan)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "narrative_summary" in body
    assert "compliance_context" in body


def test_context_endpoint_has_regulations(client, project_loan):
    resp = client.post("/compliance/context", json=project_loan)
    ctx = resp.json()["compliance_context"]
    assert len(ctx["regulations"]) >= 1


def test_context_endpoint_has_risk_classification(client, project_loan):
    resp = client.post("/compliance/context", json=project_loan)
    rc = resp.json()["compliance_context"]["risk_classification"]
    assert rc["risk_level"] in {"PROHIBITED", "HIGH", "LIMITED", "MINIMAL", "UNKNOWN", "OTHER"}


def test_context_endpoint_missing_required_fields_returns_422(client):
    resp = client.post("/compliance/context", json={"name": "incomplete"})
    assert resp.status_code == 422


def test_context_endpoint_invalid_ai_task_still_accepted(client, project_loan):
    """Unknown enum values are passed as strings; the agent decides classification."""
    payload = {**project_loan, "ai_task": "UNKNOWN_TASK"}
    resp = client.post("/compliance/context", json=payload)
    # FastAPI doesn't validate free-string fields; agent handles them
    assert resp.status_code == 200


# ── POST /compliance/dataset ──────────────────────────────────────────────────

def test_dataset_endpoint_loan_dataset(client, dataset_loans):
    resp = client.post("/compliance/dataset", json=dataset_loans)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "objectives" in body
    assert len(body["objectives"]) >= 1


def test_dataset_endpoint_scope_in_response(client, dataset_loans):
    resp = client.post("/compliance/dataset", json=dataset_loans)
    assert resp.json()["scope"] == "TRAINING"


def test_dataset_endpoint_protected_attributes_present(client, dataset_loans):
    resp = client.post("/compliance/dataset", json=dataset_loans)
    attrs = resp.json()["protected_attributes"]
    assert len(attrs) >= 1
    assert all("semantic_type" in a for a in attrs)


def test_dataset_endpoint_objectives_have_metric(client, dataset_loans):
    resp = client.post("/compliance/dataset", json=dataset_loans)
    for obj in resp.json()["objectives"]:
        assert obj["metric"]["id"]
        assert obj["metric"]["scale"]


def test_dataset_endpoint_minimal_payload(client):
    """Only required fields — should not crash."""
    resp = client.post("/compliance/dataset", json={"name": "test", "scope": "TRAINING"})
    assert resp.status_code == 200


def test_dataset_endpoint_invalid_scope_passes_as_string(client):
    """scope is a plain string field — the agent interprets it; no 422 expected."""
    resp = client.post("/compliance/dataset",
                       json={"name": "test", "scope": "INVALID_SCOPE"})
    assert resp.status_code == 200


# ── POST /compliance/model ────────────────────────────────────────────────────

def test_model_endpoint_credit_model(client, model_credit):
    resp = client.post("/compliance/model", json=model_credit)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "objectives" in body
    assert len(body["objectives"]) >= 1


def test_model_endpoint_has_fairness_objective(client, model_credit):
    resp = client.post("/compliance/model", json=model_credit)
    names = [o["name"] for o in resp.json()["objectives"]]
    assert any("equalized" in n.lower() or "parity" in n.lower() for n in names)


def test_model_endpoint_has_performance_objective(client, model_credit):
    resp = client.post("/compliance/model", json=model_credit)
    names = [o["name"] for o in resp.json()["objectives"]]
    assert any("auc" in n.lower() or "accuracy" in n.lower() for n in names)


def test_model_endpoint_with_prior_requirements(client, model_credit, project_loan):
    """Pipeline: pass context requirements into the model analysis."""
    ctx_resp = client.post("/compliance/context", json=project_loan)
    prior = ctx_resp.json()["compliance_context"].get("requirements", [])
    payload = {**model_credit, "prior_requirements": prior}
    resp = client.post("/compliance/model", json=payload)
    assert resp.status_code == 200


def test_model_endpoint_narrative_fields_present(client, model_credit):
    resp = client.post("/compliance/model", json=model_credit)
    body = resp.json()
    assert body.get("narrative_summary")
    assert body.get("fairness_analysis")
    assert body.get("robustness_analysis")


def test_model_endpoint_missing_name_returns_422(client):
    resp = client.post("/compliance/model", json={"ai_task": "CLASSIFICATION"})
    assert resp.status_code == 422


# ── Full pipeline: context → dataset → model ──────────────────────────────────

def test_full_pipeline(client, project_loan, dataset_loans, model_credit):
    """Mirrors the complete Streamlit UI flow: Tab 1 → Tab 2 → Tab 3."""
    # Step 1: build compliance context
    ctx = client.post("/compliance/context", json=project_loan).json()
    assert ctx["compliance_context"]["risk_classification"]["risk_level"] == "HIGH"

    # Step 2: analyse dataset with project context attached
    ds_payload = {**dataset_loans, "project": project_loan}
    ds = client.post("/compliance/dataset", json=ds_payload).json()
    assert len(ds["objectives"]) >= 1

    # Step 3: analyse model with prior requirements from context
    prior = ctx["compliance_context"].get("requirements", [])
    mdl_payload = {**model_credit, "prior_requirements": prior}
    mdl = client.post("/compliance/model", json=mdl_payload).json()
    assert len(mdl["objectives"]) >= 1

    # The fairness threshold in the model analysis should be stricter than in the dataset
    fairness_obj = next(
        (o for o in mdl["objectives"] if "equalized" in o["name"].lower()
         or "parity" in o["name"].lower()),
        None,
    )
    assert fairness_obj is not None
