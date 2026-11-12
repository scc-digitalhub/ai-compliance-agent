# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Output contracts stay aligned with okb/schemas and the skill examples stay valid."""
from __future__ import annotations

import json
import typing
from importlib.resources import files
from pathlib import Path

import pytest

from compliance_core.contracts import common, enums, requests, results
from compliance_core.contracts import (
    DatasetAgentOutput,
    ModelAgentOutput,
    ProjectContextAgentOutput,
)
from compliance_core.contracts.common import ObjectiveConditionOut

OKB = Path(str(files("compliance_core").joinpath("data", "okb", "schemas")))


def example(skill: str) -> dict:
    return json.loads(
        Path(str(files("compliance_skills").joinpath("skills", skill, "references", "example.json"))).read_text()
    )


def okb_props(schema: str) -> dict:
    data = json.loads((OKB / f"{schema}.json").read_text())
    props = dict(data.get("properties", {}))
    for part in data.get("allOf", []):
        if "$ref" in part:
            props.update(okb_props(part["$ref"].removesuffix(".json")))
    return props


def okb_enum(schema: str, *path: str) -> list[str]:
    node = okb_props(schema)[path[0]]
    for key in path[1:]:
        node = node["items"] if key == "items" else node["properties"][key]
    return node.get("enum") or node["items"]["enum"]


ENUM_CASES = [
    ("Metric", ("kind",), enums.MetricKind),
    ("Metric", ("scale",), enums.MetricScale),
    ("ObjectiveCondition", ("threshold", "operator"), enums.ThresholdOperator),
    ("ComplianceObjective", ("priority",), enums.Priority),
    ("ComplianceObjective", ("severity",), enums.Severity),
    ("AttributeRef", ("semantic_type",), enums.SemanticType),
    ("AttributeRef", ("attribute_role",), enums.AttributeRole),
    ("AttributeRef", ("observability",), enums.Observability),
    ("AttributeRef", ("use_permissions", "items"), enums.UsePermission),
    ("GroupSpec", ("group_kind",), enums.GroupKind),
    ("GroupSpec", ("group_role",), enums.GroupRole),
    ("GroupSpec", ("vulnerability",), enums.Vulnerability),
    ("Requirement", ("kind",), enums.RequirementKind),
    ("Requirement", ("applicability_status",), enums.ApplicabilityStatus),
    ("RiskClassification", ("risk_level",), enums.RiskLevel),
    ("RiskClassification", ("classification_status",), enums.ClassificationStatus),
    ("HumanOversightProfile", ("oversight_mode",), enums.OversightMode),
    ("HumanOversightProfile", ("intervention_points", "items"), enums.InterventionPoint),
    ("HumanOversightProfile", ("authority", "items"), enums.OversightAuthority),
    ("HumanOversightProfile", ("availability",), enums.OversightAvailability),
    ("HumanOversightProfile", ("escalation_channels", "items"), enums.EscalationChannel),
    ("MisuseScenario", ("misuse_kind",), enums.MisuseKind),
    ("MisuseScenario", ("intentionality",), enums.Intentionality),
    ("MisuseScenario", ("likelihood",), enums.Likelihood),
    ("MisuseScenario", ("impact",), enums.Impact),
    ("ComplianceContext", ("environment",), enums.Environment),
    ("ComplianceContext", ("actor_role",), enums.ActorRole),
    ("HumanOversightProfile", ("overseer_roles", "items"), enums.ActorRole),
    ("ProjectComplianceSpec", ("ai_task",), enums.AiTask),
    ("ProjectComplianceSpec", ("deployment",), enums.Deployment),
    ("DataComplianceSpec", ("scope",), enums.DatasetScope),
]


@pytest.mark.parametrize("schema,path,alias", ENUM_CASES, ids=lambda v: str(v)[:40])
def test_enums_match_okb(schema, path, alias):
    assert list(typing.get_args(alias)) == okb_enum(schema, *path)


MODEL_TO_SCHEMA = [
    (results.ComplianceContextOut, "ComplianceContext", set()),
    (requests.ProjectComplianceSpec, "ProjectComplianceSpec", set()),
    (requests.DomainDescriptor, "DomainDescriptor", set()),
    (results.DataComplianceOut, "DataComplianceSpec", set()),
    (common.RequirementOut, "Requirement", set()),
    (common.AttributeRefOut, "AttributeRef", {"rationale"}),
    (common.GroupSpecOut, "GroupSpec", set()),
    (common.MisuseScenarioOut, "MisuseScenario", set()),
    (common.HumanOversightOut, "HumanOversightProfile", set()),
    (common.RiskClassificationOut, "RiskClassification", set()),
    (common.MetricOut, "Metric", set()),
    (common.ComplianceObjectiveOut, "ComplianceObjective", {"rationale"}),
]


@pytest.mark.parametrize("model,schema,extras", MODEL_TO_SCHEMA, ids=lambda v: getattr(v, "__name__", str(v)))
def test_fields_exist_in_okb(model, schema, extras):
    unknown = set(model.model_fields) - set(okb_props(schema)) - extras
    assert not unknown, f"{model.__name__} has fields not in okb/{schema}: {unknown}"


@pytest.mark.parametrize(
    "skill,model",
    [("project-context", ProjectContextAgentOutput), ("dataset-analysis", DatasetAgentOutput), ("model-analysis", ModelAgentOutput)],
)
def test_skill_example_is_valid_output(skill, model):
    model.model_validate(example(skill))


def test_condition_requires_exactly_one():
    ObjectiveConditionOut(threshold={"operator": "GEQ", "value": 1})
    with pytest.raises(ValueError):
        ObjectiveConditionOut()
    with pytest.raises(ValueError):
        ObjectiveConditionOut(threshold={"operator": "GEQ", "value": 1}, range={"lower": 0, "upper": 1})


def test_invalid_enum_is_rejected():
    data = example("project-context")
    data["result"]["human_oversight"]["oversight_mode"] = "HUMAN_ON_THE_LOOP"
    with pytest.raises(ValueError):
        ProjectContextAgentOutput.model_validate(data)


def test_project_input_round_trips_through_the_dh_project_specification():
    project = requests.ProjectInput(
        name="credit", domain="finance", ai_task="classification", goal="g", geography=["IT"], environment="pilot"
    )
    context = results.ComplianceContextOut.model_validate(
        {**example("project-context")["result"], "geography": ["IT"], "environment": "PILOT"}
    )

    spec = requests.ProjectComplianceSpec.of(project, context)

    assert project.domain.domain == "finance" and project.ai_task == "CLASSIFICATION"
    assert "name" not in spec.model_dump() and "geography" not in spec.model_dump()
    assert spec.project("credit") == project  # geography and environment come back from the context
