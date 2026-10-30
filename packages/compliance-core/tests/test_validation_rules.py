from __future__ import annotations

import copy
import json
from importlib.resources import files

import pytest

from compliance_core.contracts import DatasetAnalysisRequest, ProjectContextAgentOutput, ProjectInput
from compliance_core.contracts.results import DataComplianceOut
from compliance_core.knowledge import get_bundle
from compliance_core.validation import validate_context, validate_dataset


def example(skill: str) -> dict:
    return json.loads(files("compliance_skills").joinpath("skills", skill, "references", "example.json").read_text())


PROJECT = ProjectInput(name="credit", domain="finance", ai_task="CLASSIFICATION", goal="Score loans")


def context_issues(mutate) -> list:
    output = copy.deepcopy(example("project-context"))
    mutate(output["result"])
    result = ProjectContextAgentOutput.model_validate(output).result
    return validate_context(result, PROJECT, get_bundle())


def messages(issues, severity):
    return [issue.message for issue in issues if issue.severity == severity]


def test_the_reference_example_passes_without_issues():
    assert context_issues(lambda result: None) == []


def test_requirement_attributed_to_the_wrong_framework_is_an_error():
    def mutate(result):
        result["regulations"].append({"framework": "GDPR"})
        result["requirements"][0]["source"]["framework"] = "GDPR"

    errors = messages(context_issues(mutate), "error")
    assert any("belongs to framework 'EU_AI_ACT'" in message for message in errors)


def test_requirement_citing_an_undeclared_regulation_is_an_error():
    def mutate(result):
        result["regulations"] = [{"framework": "GDPR"}]

    errors = messages(context_issues(mutate), "error")
    assert any("not among the declared regulations ['GDPR']" in message for message in errors)


def test_unknown_regulation_framework_is_a_warning():
    def mutate(result):
        result["regulations"].append({"framework": "MADE_UP_ACT"})

    assert "regulation framework 'MADE_UP_ACT' is not in the OKF bundle" in messages(context_issues(mutate), "warning")


@pytest.mark.parametrize("risk", ["MINIMAL", "LIMITED"])
def test_low_risk_with_high_risk_requirements_is_a_warning(risk):
    def mutate(result):
        result["risk_classification"]["risk_level"] = risk

    warnings = messages(context_issues(mutate), "warning")
    assert any(f"risk level is {risk}" in message and "req-euai-art-14" in message for message in warnings)


def test_high_risk_without_high_risk_requirements_is_a_warning():
    def mutate(result):
        requirement = result["requirements"][0]
        requirement.update(id="req-euai-art-50", name="Art. 50", kind="TRANSPARENCY")

    warnings = messages(context_issues(mutate), "warning")
    assert any("risk level is HIGH, but no applicable EU AI Act high-risk requirement" in m for m in warnings)


def test_dataset_objectives_outside_the_project_context_are_warnings():
    context = example("project-context")["result"]
    request = DatasetAnalysisRequest.model_validate(
        {"dataset": {"name": "applications", "scope": "TRAINING"}, "project_context": context}
    )
    result = DataComplianceOut.model_validate(example("dataset-analysis")["result"])
    issues = validate_dataset(result, request, get_bundle())
    assert not messages(issues, "error")
    assert any("'req-euai-art-10', which is not among the project context" in m for m in messages(issues, "warning"))


def test_host_recording_requires_existing_cited_sources():
    from compliance_core.host_tools import record_compliance_analysis
    from compliance_core.state import InMemoryStateStore
    from compliance_core.tools import ToolEnv

    env = ToolEnv(state=InMemoryStateStore(), bundle=get_bundle())
    request = PROJECT.model_dump(mode="json")
    output = example("project-context")

    missing = record_compliance_analysis(env, "project", request, output)
    assert missing["stored"] is False and "grounding must list" in missing["errors"][0]["message"]
    for invented in ("catalog/requirements/made-up.md", "../../pyproject.toml"):
        rejected = record_compliance_analysis(env, "project", request, output, grounding=[invented])
        assert rejected["stored"] is False and "is not in the OKF bundle" in rejected["errors"][0]["message"]
    assert len(env.state) == 0

    stored = record_compliance_analysis(
        env, "project", request, output, grounding=["/catalog/requirements/eu-ai-act/art14-human-oversight.md"],
    )
    assert stored["stored"] is True
    assert stored["provenance"]["grounding"] == ["catalog/requirements/eu-ai-act/art14-human-oversight.md"]
