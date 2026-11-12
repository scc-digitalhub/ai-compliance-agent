---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: MisuseScenario
description: A foreseeable misuse scenario for an AI system, with intentionality, likelihood, and impact assessment.
tags: [context, risk, misuse, safety, adversarial]
schema: ../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`MisuseScenario` documents a specific way an AI system might be misused, the
actors who might cause it, the [groups affected](/context/GroupSpec.md), and a
qualitative risk estimate (likelihood × impact). These scenarios are collected in
[ComplianceContext](/context/ComplianceContext.md) as `foreseeable_misuse`.

Extends [BaseComplianceObject](/foundations/BaseComplianceObject.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | *(from BaseComplianceObject)* |
| `namespace` | string | no | *(from BaseComplianceObject)* |
| `name` | string | yes | *(from BaseComplianceObject)* |
| `description` | string | no | *(from BaseComplianceObject)* |
| `misuse_kind` | enum | yes | Category of misuse — see below. |
| `misuse_kind_value` | string | no | Free text when `misuse_kind` is `OTHER`. |
| `intentionality` | enum | no | `ACCIDENTAL` \| `NEGLIGENT` \| `INTENTIONAL` \| `ADVERSARIAL` \| `UNKNOWN` |
| `likelihood` | enum | no | `RARE` \| `UNLIKELY` \| `POSSIBLE` \| `LIKELY` \| `ALMOST_CERTAIN` \| `UNKNOWN` |
| `impact` | enum | no | `NEGLIGIBLE` \| `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` \| `UNKNOWN` |
| `actor_roles` | set of ActorRole | no | Roles that may cause this misuse. |
| `affected_groups` | set of [GroupSpec](/context/GroupSpec.md) | no | Groups harmed by this misuse. |
| `rationale` | string | no | Supporting analysis. |

## Misuse Kind Values

`OUT_OF_SCOPE_USE` · `OVERRELIANCE` · `AUTOMATION_BIAS` · `HUMAN_OVERSIGHT_BYPASS` ·
`DECISION_AUTOMATION_BEYOND_PURPOSE` · `UNAUTHORIZED_ACCESS` · `DATA_LEAKAGE` ·
`DATA_POISONING` · `MODEL_POISONING` · `ADVERSARIAL_INPUT` · `PROMPT_INJECTION` ·
`MODEL_EXTRACTION` · `MONITORING_EVASION` · `FEEDBACK_LOOP_AMPLIFICATION` ·
`UNSAFE_FALLBACK_USE` · `MISINTERPRETATION_OF_OUTPUT` ·
`DEPLOYMENT_IN_UNVALIDATED_CONTEXT` · `OTHER`
