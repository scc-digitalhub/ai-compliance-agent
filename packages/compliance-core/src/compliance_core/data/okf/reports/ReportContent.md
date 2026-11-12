---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ReportContent
description: Content envelope for a compliance report — wraps exactly one of EvaluationContent, TestContent, or LogContent.
tags: [report, evidence, evaluation, test, log]
schema: ../okb/schemas/ReportContent.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ReportContent` is the content payload of a Report entity. Exactly one of the
three content variants should be populated. It carries a [Lineage](/foundations/Lineage.md)
reference to trace where the report came from, and links back to the
[ComplianceObjective](/objectives/ComplianceObjective.md)s it addresses via string
identifiers.

The Report itself (a platform first-class entity) wraps this spec alongside identity,
versioning, audit, and validity timestamps.

# Schema

Exactly one of the following content fields should be populated:

| Field | Type | Description |
|-------|------|-------------|
| `evaluation` | EvaluationContent | Metric measurement results. |
| `test` | TestContent | Compliance test outcomes. |
| `log` | LogContent | Inference log window. |

## EvaluationContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metrics` | list of [MetricResult](/metrics/MetricResult.md) | no | Observed metric values. |
| `summary` | string | no | Narrative summary. |

## TestContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `results` | list of TestResult | no | Per-objective test results. |
| `verdict` | enum | yes | `PASS` \| `FAIL` \| `INCONCLUSIVE` \| `ERROR` |
| `summary` | string | no | Narrative summary. |

### TestResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `measured` | string | yes | Serialised observed value. |
| `expected` | [ObjectiveCondition](/objectives/ObjectiveCondition.md) | yes | Snapshot of the condition at evaluation time. |
| `passed` | boolean | yes | Whether the condition was satisfied. |
| `details` | string | no | Additional detail. |

## LogContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | enum | yes | `INPUT_OUTPUT` \| `RESOURCE` \| `EVENT` \| `AUDIT` |
| `window` | TimeWindow | yes | `{ from: datetime, to: datetime }` observation window. |
