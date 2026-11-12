---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Objective
title: ComplianceObjective
description: Normative constraint binding a Metric to a target acceptance condition, with priority, severity, and links to requirements.
tags: [objective, compliance, metric, requirement, acceptance-criterion]
schema: ../okb/schemas/ComplianceObjective.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceObjective` is the acceptance criterion of the framework. It names a
[Metric](/metrics/Metric.md), prescribes an [ObjectiveCondition](/objectives/ObjectiveCondition.md)
it must satisfy, and lists the [Requirement](/context/Requirement.md) identifiers
it operationalises.

Objectives are collected in [ComplianceSpec](/specs/ComplianceSpec.md) and
referenced from [ComplianceFinding](/compliance/ComplianceFinding.md) (by `id`)
when a violation is detected.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name of the objective. |
| `description` | string | no | Narrative description. |
| `metric` | [Metric](/metrics/Metric.md) | yes | Metric that is evaluated (embedded). |
| `condition` | [ObjectiveCondition](/objectives/ObjectiveCondition.md) | yes | Acceptance condition. |
| `priority` | enum | yes | `MANDATORY` \| `RECOMMENDED` \| `INFORMATIONAL` |
| `severity` | enum | yes | `CRITICAL` \| `HIGH` \| `MEDIUM` \| `LOW` \| `INFO` |
| `requirements` | set of string | no | Identifiers of [Requirement](/context/Requirement.md) objects this objective operationalises. |

# Examples

```json
{
  "name": "Demographic Parity Difference ≤ 0.05",
  "metric": { "id": "dpd-001", "name": "Demographic Parity Difference", "kind": "PRIMITIVE", "scale": "RATIO" },
  "condition": { "threshold": { "operator": "LEQ", "value": 0.05 } },
  "priority": "MANDATORY",
  "severity": "HIGH",
  "requirements": ["req-eu-ai-art10"]
}
```
