"""Tests for Pydantic output schema validation."""
from __future__ import annotations

import pytest
from tests.conftest import _make_context_response, _make_dataset_response, _make_model_response


# ── ComplianceContextResponse ─────────────────────────────────────────────────

def test_context_response_valid():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    assert obj.compliance_context.environment == "PRODUCTION"
    assert len(obj.compliance_context.regulations) == 2
    assert obj.compliance_context.risk_classification.risk_level == "HIGH"


def test_context_response_regulations_have_framework():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    for reg in obj.compliance_context.regulations:
        assert reg.framework, "framework must be non-empty"


def test_context_response_requirements_have_source():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    for req in obj.compliance_context.requirements:
        assert req.source.framework


def test_context_response_groups_have_kind_and_role():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    for g in obj.compliance_context.affected_groups + obj.compliance_context.vulnerable_groups:
        assert g.group_kind
        assert g.group_role


def test_context_response_protected_attributes():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    for attr in obj.compliance_context.protected_attributes:
        assert attr.semantic_type
        assert attr.attribute_role


def test_context_response_human_oversight_has_mode():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    assert obj.compliance_context.human_oversight.oversight_mode


def test_context_response_missing_narrative_raises():
    from agent.schemas import ComplianceContextResponse
    from pydantic import ValidationError
    data = _make_context_response()
    del data["narrative_summary"]
    with pytest.raises(ValidationError):
        ComplianceContextResponse(**data)


# ── DataComplianceResponse ────────────────────────────────────────────────────

def test_dataset_response_valid():
    from agent.schemas import DataComplianceResponse
    obj = DataComplianceResponse(**_make_dataset_response())
    assert obj.scope == "TRAINING"
    assert len(obj.protected_attributes) >= 1
    assert len(obj.objectives) >= 1


def test_dataset_objectives_have_metric_and_condition():
    from agent.schemas import DataComplianceResponse
    obj = DataComplianceResponse(**_make_dataset_response())
    for o in obj.objectives:
        assert o.metric.id
        assert o.metric.scale
        assert o.condition.threshold or o.condition.range or o.condition.categorical


def test_dataset_objectives_priority_is_valid():
    from agent.schemas import DataComplianceResponse
    valid = {"MANDATORY", "RECOMMENDED", "INFORMATIONAL"}
    obj = DataComplianceResponse(**_make_dataset_response())
    for o in obj.objectives:
        assert o.priority in valid


def test_dataset_objectives_severity_is_valid():
    from agent.schemas import DataComplianceResponse
    valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
    obj = DataComplianceResponse(**_make_dataset_response())
    for o in obj.objectives:
        assert o.severity in valid


# ── ModelComplianceResponse ───────────────────────────────────────────────────

def test_model_response_valid():
    from agent.schemas import ModelComplianceResponse
    obj = ModelComplianceResponse(**_make_model_response())
    assert len(obj.objectives) == 2


def test_model_fairness_objective_threshold():
    from agent.schemas import ModelComplianceResponse
    obj = ModelComplianceResponse(**_make_model_response())
    eod = next(o for o in obj.objectives if "Equalized" in o.name)
    assert eod.condition.threshold.operator == "LEQ"
    assert eod.condition.threshold.value == 0.05
    assert eod.priority == "MANDATORY"
    assert eod.severity == "CRITICAL"


def test_model_performance_objective_threshold():
    from agent.schemas import ModelComplianceResponse
    obj = ModelComplianceResponse(**_make_model_response())
    auc = next(o for o in obj.objectives if "AUC" in o.name)
    assert auc.condition.threshold.operator == "GEQ"
    assert auc.condition.threshold.value == 0.85


def test_model_objectives_link_requirements():
    from agent.schemas import ModelComplianceResponse
    obj = ModelComplianceResponse(**_make_model_response())
    for o in obj.objectives:
        assert len(o.requirements) >= 1, f"Objective '{o.name}' has no linked requirements"


# ── ObjectiveCondition mutual exclusivity ─────────────────────────────────────

def test_objective_condition_threshold_only():
    from agent.schemas import ObjectiveConditionOut, ThresholdConditionOut
    cond = ObjectiveConditionOut(
        threshold=ThresholdConditionOut(operator="GEQ", value=0.85)
    )
    assert cond.threshold is not None
    assert cond.range is None


def test_objective_condition_range_only():
    from agent.schemas import ObjectiveConditionOut, RangeConditionOut
    cond = ObjectiveConditionOut(
        range=RangeConditionOut(lower=0.0, upper=0.05, inclusive=True)
    )
    assert cond.range is not None
    assert cond.threshold is None


# ── Serialisation round-trip ──────────────────────────────────────────────────

def test_context_response_json_round_trip():
    from agent.schemas import ComplianceContextResponse
    obj = ComplianceContextResponse(**_make_context_response())
    json_str = obj.model_dump_json()
    restored = ComplianceContextResponse.model_validate_json(json_str)
    assert restored.compliance_context.risk_classification.risk_level == "HIGH"


def test_dataset_response_json_round_trip():
    from agent.schemas import DataComplianceResponse
    obj = DataComplianceResponse(**_make_dataset_response())
    json_str = obj.model_dump_json()
    restored = DataComplianceResponse.model_validate_json(json_str)
    assert restored.scope == "TRAINING"
