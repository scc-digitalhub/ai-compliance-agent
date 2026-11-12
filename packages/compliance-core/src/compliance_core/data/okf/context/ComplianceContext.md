---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Context
title: ComplianceContext
description: Contextualizes an AI project's deployment with respect to regulations, risk, affected groups, and oversight.
tags: [context, regulation, risk, oversight, fairness]
schema: ../okb/schemas/ComplianceContext.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceContext` is the central anchor for all compliance-relevant properties
of a deployment scenario. A single project may have multiple contexts (production,
sandbox, pilot). Each context independently specifies the applicable
[regulations](/foundations/RegulatoryRef.md), [risk level](/context/RiskClassification.md),
[affected groups](/context/GroupSpec.md), [oversight mode](/context/HumanOversightProfile.md),
and set of [requirements](/context/Requirement.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `environment` | enum | yes | `PRODUCTION` \| `SANDBOX` \| `PILOT` |
| `regulations` | set of [RegulatoryRef](/foundations/RegulatoryRef.md) | no | Applicable regulatory frameworks. |
| `geography` | set of string | no | Jurisdictions of deployment (ISO 3166-1 codes recommended). |
| `actor_role` | [ActorRole](#actor-role-values) | no | Role of the organisation or party in this context. |
| `actor_role_value` | string | no | Free-text role when `actor_role` is `OTHER`. |
| `affected_groups` | set of [GroupSpec](/context/GroupSpec.md) | no | Groups directly affected by the system. |
| `vulnerable_groups` | set of [GroupSpec](/context/GroupSpec.md) | no | Subset of affected groups with heightened vulnerability. |
| `protected_attributes` | set of [AttributeRef](/context/AttributeRef.md) | no | Attributes subject to non-discrimination or privacy protections. |
| `foreseeable_misuse` | set of [MisuseScenario](/context/MisuseScenario.md) | no | Foreseeable misuse scenarios. |
| `human_oversight` | [HumanOversightProfile](/context/HumanOversightProfile.md) | no | Oversight configuration. |
| `risk_classification` | [RiskClassification](/context/RiskClassification.md) | no | Risk level and classification status. |
| `requirements` | set of [Requirement](/context/Requirement.md) | no | Applicable normative requirements. |

## Actor Role Values

`PROVIDER` · `DEPLOYER` · `DISTRIBUTOR` · `AUTHORIZED_REPRESENTATIVE` ·
`PRODUCT_MANUFACTURER` · `MODEL_DEVELOPER` · `SYSTEM_INTEGRATOR` ·
`SERVICE_OPERATOR` · `DATA_PROVIDER` · `DATA_CONTROLLER` · `DATA_PROCESSOR` ·
`HUMAN_OVERSIGHT_OPERATOR` · `END_USER` · `AFFECTED_PERSON` · `COMPLIANCE_OWNER` · `OTHER`
