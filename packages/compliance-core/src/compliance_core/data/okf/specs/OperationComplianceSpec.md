---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Specification Container
title: OperationComplianceSpec
description: Compliance extension for an operation/function entity, classifying the operation by mode, type, category, and lifecycle phase, and linking it to the compliance objectives it validates or mitigates.
tags: [spec, operation, compliance, validation, mitigation, lifecycle]
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`OperationComplianceSpec` is the compliance extension for an **operation / function**
entity (`kind: operation-compliance`, `appliesTo: ["function"]`). Unlike the other
spec containers, it extends `BaseSpec` directly rather than
[ComplianceSpec](ComplianceSpec.md), because operations are *producers*
of compliance evidence, not *subjects* of it.

The spec classifies the operation along four axes:

| Axis | Field | Description |
|------|-------|-------------|
| Execution mode | `mode` | Whether the operation runs as a one-shot job or a long-running service. |
| Compliance type | `type` | Whether it *validates* objectives or *mitigates* violations. |
| Functional category | `category` | The specific operation kind from the taxonomy (§4). |
| Lifecycle phase | `phase` | The AI lifecycle stage in which the operation runs. |

The `objectives` set links this operation to the
[ComplianceObjective](/objectives/ComplianceObjective.md) entities it addresses,
referenced via [EntityRef](/foundations/EntityRef.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | enum | no | `JOB` \| `SERVICE` |
| `type` | enum | no | `VALIDATION` \| `MITIGATION` |
| `category` | enum | no | Functional category — see below. |
| `phase` | enum | no | `DATA_PREPARATION` \| `MODEL_DEVELOPMENT` \| `OPERATIONALIZATION` |
| `objectives` | set of [EntityRef](/foundations/EntityRef.md) | no | References to the compliance objectives this operation validates or mitigates. |

## Operation Category Values

### Data Preparation
`DATA_PROFILING` · `DATA_VALIDATION` · `DATA_PREPROCESSING` ·
`DOCUMENTATION_GENERATION` · `SYNTHETIC_GENERATION` · `AUGMENTATION` · `ANONYMIZATION`

### Model Development
`FEATURE_EVALUATION` · `MODEL_TRAINING` · `TRAINING_AUGMENTATION` ·
`MODEL_PROFILING` · `RESOURCE_PROFILING` · `MODEL_VALIDATION`

### Operationalization
`GUARDRAIL` · `PREPROCESSING` · `POSTPROCESSING` ·
`INPUT_TRACING` · `OUTPUT_TRACING` · `RESOURCE_MONITORING` ·
`DRIFT_DETECTION` · `LOG_ANALYSIS`

# Relationship to Operation Taxonomy

This spec maps directly to the compliance operation taxonomy in
[§4 of the framework](/AI Compliance Framework.md). The table below shows the
mapping for key operations:

| Category | type | mode | phase |
|----------|------|------|-------|
| `DATA_VALIDATION` | `VALIDATION` | `JOB` | `DATA_PREPARATION` |
| `MODEL_VALIDATION` | `VALIDATION` | `JOB` | `MODEL_DEVELOPMENT` |
| `SYNTHETIC_GENERATION` | `MITIGATION` | `JOB` | `DATA_PREPARATION` |
| `ANONYMIZATION` | `MITIGATION` | `JOB` | `DATA_PREPARATION` |
| `TRAINING_AUGMENTATION` | `MITIGATION` | `JOB` | `MODEL_DEVELOPMENT` |
| `GUARDRAIL` | `MITIGATION` | `JOB` | `OPERATIONALIZATION` |
| `INPUT_TRACING` | — | `SERVICE` | `OPERATIONALIZATION` |
| `DRIFT_DETECTION` | `MITIGATION` | `JOB` | `OPERATIONALIZATION` |

# Examples

```json
{
  "mode": "JOB",
  "type": "VALIDATION",
  "category": "MODEL_VALIDATION",
  "phase": "MODEL_DEVELOPMENT",
  "objectives": [
    { "key": "compliance-objective::eod-check-001" },
    { "key": "compliance-objective::dpd-check-001" }
  ]
}
```
