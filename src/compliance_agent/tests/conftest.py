"""Shared fixtures and helpers for the compliance agent test suite."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── Make src/compliance_agent importable from tests/ ──────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Point OKF at the real bundle so tool tests exercise actual files
OKF_PATH = ROOT.parent.parent / "okf"
os.environ.setdefault("OKF_BUNDLE_PATH", str(OKF_PATH))
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("AGENT_VERBOSE", "false")


# ── Domain fixtures matching the Streamlit UI example scenarios ────────────────

@pytest.fixture()
def project_loan() -> dict:
    """Finance / CLASSIFICATION — mirrors Streamlit Tab-1 default."""
    return {
        "name": "AI Loan Approval System",
        "domain": "finance",
        "ai_task": "CLASSIFICATION",
        "goal": "Automate creditworthiness assessment for retail loan applications.",
        "purpose": "Streamline credit decision-making for loan officers",
        "audience": "Retail banking customers and loan officers",
        "deployment": "CLOUD",
        "environment": "PRODUCTION",
        "geography": ["IT", "EU"],
        "scope_in": ["Credit scoring", "Application screening"],
        "scope_out": ["Final lending decision", "Fraud investigation"],
    }


@pytest.fixture()
def dataset_loans() -> dict:
    """TRAINING dataset with PII/sensitive fields — mirrors Streamlit Tab-2 default."""
    return {
        "name": "loan_applications_2023",
        "description": "Historical retail loan application records.",
        "scope": "TRAINING",
        "domain": "finance",
        "sensitivity": "PII",
        "n_records": 120000,
        "schema_fields": [
            {"name": "applicant_id", "dtype": "STRING",  "sensitivity": "NONE",      "nullable": False},
            {"name": "age",          "dtype": "INT",     "sensitivity": "PII",       "nullable": False},
            {"name": "gender",       "dtype": "STRING",  "sensitivity": "SENSITIVE", "nullable": True},
            {"name": "nationality",  "dtype": "STRING",  "sensitivity": "SENSITIVE", "nullable": True},
            {"name": "marital_status","dtype": "STRING", "sensitivity": "PII",       "nullable": True},
            {"name": "income_annual","dtype": "FLOAT",   "sensitivity": "PII",       "nullable": False},
            {"name": "credit_score", "dtype": "INT",     "sensitivity": "PII",       "nullable": False},
            {"name": "loan_amount",  "dtype": "FLOAT",   "sensitivity": "NONE",      "nullable": False},
            {"name": "loan_purpose", "dtype": "STRING",  "sensitivity": "NONE",      "nullable": True},
            {"name": "outcome",      "dtype": "INT",     "sensitivity": "NONE",      "nullable": False},
        ],
        "sample_records": [
            {"applicant_id": "X001", "age": 34, "gender": "F",
             "nationality": "IT", "income_annual": 38000,
             "credit_score": 680, "outcome": 1},
        ],
        "known_protected_attributes": ["gender", "nationality", "age", "marital_status"],
    }


@pytest.fixture()
def model_credit() -> dict:
    """BINARY_CLASSIFICATION XGBoost model — mirrors Streamlit Tab-3 default."""
    return {
        "name": "credit_xgboost_v2",
        "description": "XGBoost binary classifier predicting loan approval probability.",
        "ai_task": "CLASSIFICATION",
        "domain": "finance",
        "framework": "XGBOOST",
        "output_type": "BINARY_CLASSIFICATION",
        "produces_probabilities": True,
        "trained_on_sensitive_data": True,
        "known_affected_groups": ["retail banking customers", "loan applicants"],
        "prior_requirements": [],
    }


# ── Canned structured responses (no LLM needed) ───────────────────────────────

def _make_context_response() -> dict:
    return {
        "narrative_summary": "High-risk AI under EU AI Act Annex III §5(b).",
        "regulatory_analysis": "EU AI Act, GDPR Art. 22, EBA ML guidelines apply.",
        "risk_analysis": "Classified HIGH-risk; DPIA required.",
        "oversight_analysis": "Human-in-the-loop review required for all decisions.",
        "compliance_context": {
            "environment": "PRODUCTION",
            "regulations": [
                {"framework": "EU_AI_ACT", "article": "Art. 10", "version": "2024/1689"},
                {"framework": "GDPR", "article": "Art. 22", "version": "2016/679"},
            ],
            "geography": ["IT", "EU"],
            "actor_role": "PROVIDER",
            "requirements": [
                {
                    "id": "req-euai-art-10",
                    "name": "EU AI Act Art. 10 — Data Governance",
                    "source": {"framework": "EU_AI_ACT", "article": "Art. 10", "version": "2024/1689"},
                    "requirement_text": "Training datasets shall be subject to data governance.",
                    "kind": "DATA_GOVERNANCE",
                    "applicability_status": "APPLICABLE",
                    "related_requirements": [],
                }
            ],
            "affected_groups": [
                {"id": "group-loan-applicants", "name": "Loan Applicants",
                 "group_kind": "DEMOGRAPHIC", "group_role": "DECISION_SUBJECT"},
            ],
            "vulnerable_groups": [
                {"id": "group-economically-disadvantaged", "name": "Economically Disadvantaged",
                 "group_kind": "VULNERABLE", "group_role": "TARGET_SUBJECT",
                 "vulnerability": "ECONOMIC_DEPENDENCY"},
            ],
            "protected_attributes": [
                {"id": "attr-gender", "name": "Gender",
                 "semantic_type": "GENDER", "attribute_role": "PROTECTED_ATTRIBUTE",
                 "observability": "SELF_REPORTED", "use_permissions": ["FAIRNESS_TESTING"]},
            ],
            "foreseeable_misuse": [
                {"id": "misuse-proxy-discrimination", "name": "Proxy Discrimination in Credit",
                 "misuse_kind": "OUT_OF_SCOPE_USE", "intentionality": "ACCIDENTAL",
                 "likelihood": "LIKELY", "impact": "HIGH"},
            ],
            "risk_classification": {"risk_level": "HIGH", "classification_status": "PRELIMINARY",
                                    "rationale": "Creditworthiness AI is Annex III high-risk."},
            "human_oversight": {"oversight_mode": "HUMAN_IN_THE_LOOP",
                                "overseer_roles": ["DEPLOYER"],
                                "intervention_points": ["DECISION_APPROVAL"],
                                "authority": ["APPROVE", "REJECT"],
                                "availability": "BUSINESS_HOURS",
                                "escalation_channels": ["COMPLIANCE_REVIEW"]},
        },
    }


def _make_dataset_response() -> dict:
    return {
        "narrative_summary": "Training dataset with SENSITIVE demographic fields.",
        "data_quality_analysis": "Completeness >= 0.95 required; label balance ratio checked.",
        "privacy_analysis": "GDPR Art. 9 special categories present (gender, nationality).",
        "fairness_analysis": "Demographic parity difference must be evaluated at training time.",
        "scope": "TRAINING",
        "protected_attributes": [
            {"id": "attr-gender", "name": "Gender", "semantic_type": "GENDER",
             "attribute_role": "PROTECTED_ATTRIBUTE", "observability": "SELF_REPORTED",
             "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL"]},
        ],
        "objectives": [
            {
                "name": "Dataset Completeness ≥ 0.95",
                "description": "At least 95% of required field values must be non-null.",
                "metric": {"id": "metric-data-completeness", "name": "Dataset Completeness",
                           "kind": "PRIMITIVE", "scale": "RATIO",
                           "unit": {"symbol": "%", "name": "percent"},
                           "range": {"lower": 0.0, "upper": 1.0, "discrete": False}},
                "condition": {"threshold": {"operator": "GEQ", "value": 0.95}},
                "priority": "MANDATORY",
                "severity": "HIGH",
                "requirements": ["req-euai-art-10"],
            },
        ],
    }


def _make_model_response() -> dict:
    return {
        "narrative_summary": "Binary classifier with high-risk profile; fairness mandatory.",
        "fairness_analysis": "Equalized odds and demographic parity must be measured per group.",
        "robustness_analysis": "Adversarial accuracy and OOD gap must be within limits.",
        "transparency_analysis": "SHAP explanations required for individual credit decisions.",
        "objectives": [
            {
                "name": "Equalized Odds Difference ≤ 0.05",
                "description": "Equal TPR and FPR across gender and nationality groups.",
                "metric": {"id": "metric-equalized-odds-difference",
                           "name": "Equalized Odds Difference",
                           "kind": "COMPOSITE", "scale": "RATIO",
                           "unit": {"symbol": "Δ", "name": "rate difference"},
                           "range": {"lower": 0.0, "upper": 1.0, "discrete": False}},
                "condition": {"threshold": {"operator": "LEQ", "value": 0.05}},
                "priority": "MANDATORY",
                "severity": "CRITICAL",
                "requirements": ["req-euai-art-10", "req-eucharter-art-21"],
            },
            {
                "name": "AUC-ROC ≥ 0.85",
                "description": "Minimum discriminative accuracy for the credit model.",
                "metric": {"id": "metric-auc-roc", "name": "AUC-ROC",
                           "kind": "PRIMITIVE", "scale": "RATIO",
                           "unit": {"symbol": "AUC", "name": "area"},
                           "range": {"lower": 0.0, "upper": 1.0, "discrete": False}},
                "condition": {"threshold": {"operator": "GEQ", "value": 0.85}},
                "priority": "MANDATORY",
                "severity": "HIGH",
                "requirements": ["req-euai-art-15"],
            },
        ],
    }


@pytest.fixture()
def mock_agent(monkeypatch):
    """Replace ComplianceAgent._run and _extract_structured with canned returns."""
    from unittest.mock import MagicMock
    import agent.schemas as schemas

    responses = {
        "context": schemas.ComplianceContextResponse(**_make_context_response()),
        "dataset": schemas.DataComplianceResponse(**_make_dataset_response()),
        "model":   schemas.ModelComplianceResponse(**_make_model_response()),
    }

    def fake_run(self, _text: str) -> str:
        return "Canned narrative — LLM not called in unit tests."

    import agent.agent as ag

    def fake_extract(narrative, schema_cls, task_hint):
        if schema_cls is schemas.ComplianceContextResponse:
            return responses["context"]
        if schema_cls is schemas.DataComplianceResponse:
            return responses["dataset"]
        return responses["model"]

    monkeypatch.setattr(ag.ComplianceAgent, "_run", fake_run)
    monkeypatch.setattr(ag, "_extract_structured", fake_extract)
    # Prevent graph construction (no API key in tests)
    monkeypatch.setattr(ag, "_build_graph", lambda: MagicMock())
    ag.ComplianceAgent._instance = None  # reset singleton
    return responses


@pytest.fixture()
def populated_stores(tmp_path, project_loan, dataset_loans, model_credit, monkeypatch):
    """Pre-populate temp EntityStores and patch the shared stores module."""
    from store import EntityStore
    import stores as st

    proj_store = EntityStore(tmp_path, "projects")
    ds_store   = EntityStore(tmp_path, "datasets")
    mdl_store  = EntityStore(tmp_path, "models")

    proj = proj_store.create(project_loan)
    ds   = ds_store.create(dataset_loans)
    mdl  = mdl_store.create(model_credit)

    monkeypatch.setattr(st, "projects", proj_store)
    monkeypatch.setattr(st, "datasets", ds_store)
    monkeypatch.setattr(st, "models",   mdl_store)

    # Also patch the references already imported into crud/main modules
    import api.crud as crud
    monkeypatch.setattr(crud, "_projects", proj_store)
    monkeypatch.setattr(crud, "_datasets", ds_store)
    monkeypatch.setattr(crud, "_models",   mdl_store)

    return {
        "project_id": proj["id"],
        "dataset_id": ds["id"],
        "model_id":   mdl["id"],
    }
