"""Tests for ComplianceAgent tasks with mocked LLM — covers Streamlit UI scenarios."""
from __future__ import annotations

import pytest


# ── Task 1: Compliance Context (finance / CLASSIFICATION) ─────────────────────

def test_build_compliance_context_returns_response(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    from agent.schemas import ComplianceContextResponse
    assert isinstance(result, ComplianceContextResponse)


def test_context_has_regulations(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert len(result.compliance_context.regulations) >= 1


def test_context_has_eu_ai_act_regulation(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    frameworks = [r.framework for r in result.compliance_context.regulations]
    assert "EU_AI_ACT" in frameworks


def test_context_risk_level_high_for_finance_classification(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert result.compliance_context.risk_classification.risk_level == "HIGH"


def test_context_has_affected_groups(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert len(result.compliance_context.affected_groups) >= 1


def test_context_has_protected_attributes(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert len(result.compliance_context.protected_attributes) >= 1


def test_context_has_human_oversight(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert result.compliance_context.human_oversight is not None
    assert result.compliance_context.human_oversight.oversight_mode


def test_context_has_narrative_sections(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert result.narrative_summary
    assert result.regulatory_analysis
    assert result.risk_analysis


def test_context_has_misuse_scenarios(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    assert len(result.compliance_context.foreseeable_misuse) >= 1


def test_context_requirements_link_to_known_frameworks(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    known = {"EU_AI_ACT", "GDPR", "DSA", "NIS2", "ISO_42001", "NIST_AI_RMF"}
    result = ComplianceAgent.get().build_compliance_context(project_loan)
    for req in result.compliance_context.requirements:
        assert req.source.framework in known, f"Unknown framework: {req.source.framework}"


# ── Task 2: Dataset Compliance ────────────────────────────────────────────────

def test_analyze_dataset_returns_response(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    from agent.schemas import DataComplianceResponse
    assert isinstance(result, DataComplianceResponse)


def test_dataset_scope_preserved(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    assert result.scope == "TRAINING"


def test_dataset_identifies_gender_as_protected(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    attr_names = [a.name.lower() for a in result.protected_attributes]
    assert any("gender" in n for n in attr_names)


def test_dataset_has_compliance_objectives(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    assert len(result.objectives) >= 1


def test_dataset_objectives_have_threshold_conditions(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    for obj in result.objectives:
        has_condition = (obj.condition.threshold or obj.condition.range
                         or obj.condition.categorical or obj.condition.statistical)
        assert has_condition, f"Objective '{obj.name}' has no condition"


def test_dataset_has_narrative_analyses(mock_agent, dataset_loans):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_dataset(dataset_loans)
    assert result.narrative_summary
    assert result.privacy_analysis
    assert result.fairness_analysis


# ── Task 3: Model Compliance ──────────────────────────────────────────────────

def test_analyze_model_returns_response(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_model(model_credit)
    from agent.schemas import ModelComplianceResponse
    assert isinstance(result, ModelComplianceResponse)


def test_model_has_fairness_objective(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_model(model_credit)
    names = [o.name for o in result.objectives]
    assert any("equalized" in n.lower() or "parity" in n.lower() for n in names)


def test_model_has_performance_objective(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_model(model_credit)
    names = [o.name for o in result.objectives]
    assert any("auc" in n.lower() or "accuracy" in n.lower() or "f1" in n.lower()
               for n in names)


def test_model_fairness_threshold_is_strict(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_model(model_credit)
    fairness_objs = [o for o in result.objectives
                     if o.condition.threshold and o.condition.threshold.operator == "LEQ"]
    assert any(o.condition.threshold.value <= 0.1 for o in fairness_objs), \
        "At least one fairness threshold should be ≤ 0.10"


def test_model_objectives_all_mandatory_or_recommended(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    valid = {"MANDATORY", "RECOMMENDED", "INFORMATIONAL"}
    result = ComplianceAgent.get().analyze_model(model_credit)
    for obj in result.objectives:
        assert obj.priority in valid


def test_model_with_prior_requirements(mock_agent, model_credit):
    """Prior requirements from a context analysis should be accepted without error."""
    from agent.agent import ComplianceAgent
    prior = [
        {"id": "req-euai-art-10", "name": "EU AI Act Art. 10",
         "source": {"framework": "EU_AI_ACT", "article": "Art. 10", "version": "2024/1689"},
         "requirement_text": "Data governance.", "kind": "DATA_GOVERNANCE",
         "applicability_status": "APPLICABLE", "related_requirements": []},
    ]
    result = ComplianceAgent.get().analyze_model(model_credit, requirements=prior)
    assert result is not None


def test_model_has_narrative_analyses(mock_agent, model_credit):
    from agent.agent import ComplianceAgent
    result = ComplianceAgent.get().analyze_model(model_credit)
    assert result.narrative_summary
    assert result.fairness_analysis
    assert result.robustness_analysis


# ── Singleton reset between tasks ─────────────────────────────────────────────

def test_agent_singleton_reused(mock_agent, project_loan):
    from agent.agent import ComplianceAgent
    a1 = ComplianceAgent.get()
    a2 = ComplianceAgent.get()
    assert a1 is a2
