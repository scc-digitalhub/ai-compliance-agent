# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Results of the structured agents.

Each agent returns an OKB-aligned `result` plus the assumptions it made; the API moves
`assumptions` into the response metadata.
"""
from __future__ import annotations

from pydantic import Field

from .common import (
    AttributeRefOut,
    ComplianceObjectiveOut,
    GroupSpecOut,
    HumanOversightOut,
    MisuseScenarioOut,
    OutModel,
    RegulatoryRefOut,
    RequirementOut,
    RiskClassificationOut,
)
from . import enums as e


class ComplianceContextOut(OutModel):
    """Maps onto okb ComplianceContext."""

    environment: e.Environment = "PRODUCTION"
    regulations: list[RegulatoryRefOut]
    geography: list[str]
    actor_role: e.ActorRole = Field("PROVIDER", description="Role of the organisation, e.g. PROVIDER, DEPLOYER")
    actor_role_value: str | None = Field(None, description="Free text when actor_role is OTHER")
    requirements: list[RequirementOut]
    affected_groups: list[GroupSpecOut] = Field(default_factory=list)
    vulnerable_groups: list[GroupSpecOut] = Field(default_factory=list)
    protected_attributes: list[AttributeRefOut] = Field(default_factory=list)
    foreseeable_misuse: list[MisuseScenarioOut]
    risk_classification: RiskClassificationOut
    human_oversight: HumanOversightOut


class DataComplianceOut(OutModel):
    """Maps onto okb DataComplianceSpec (scope, attributes, objectives)."""

    scope: e.DatasetScope
    attributes: list[AttributeRefOut] = Field(description="Protected and sensitive attributes found in the dataset")
    objectives: list[ComplianceObjectiveOut]


class ModelComplianceOut(OutModel):
    """Maps onto okb ModelComplianceSpec (objectives)."""

    objectives: list[ComplianceObjectiveOut]


class _AgentOutput(OutModel):
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made, and facts taken from general knowledge instead of the OKF bundle",
    )


class ProjectContextAgentOutput(_AgentOutput):
    result: ComplianceContextOut


class DatasetAgentOutput(_AgentOutput):
    result: DataComplianceOut


class ModelAgentOutput(_AgentOutput):
    result: ModelComplianceOut
