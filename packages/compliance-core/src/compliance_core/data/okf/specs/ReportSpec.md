---
type: Compliance Specification Container
title: ReportSpec
description: Compliance extension for a report entity, carrying the report kind, content payload, lineage, and the set of compliance objective identifiers the report addresses.
tags: [spec, report, evidence, evaluation, test, log, compliance]
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ReportSpec` is the compliance extension for a **report** entity
(`kind: compliance-report`, `appliesTo: ["dataitem", "table", "croissant", "artifact", "model"]`).
Like [OperationComplianceSpec](OperationComplianceSpec.md), it extends `BaseSpec` directly
rather than [ComplianceSpec](ComplianceSpec.md), because a report is an *evidence artefact*
produced by validation or monitoring operations — not a subject of compliance assessment.

A report is always associated with one or more
[ComplianceObjective](/objectives/ComplianceObjective.md)s (via the `objectives` set of
string identifiers) and carries its full content payload as a
[ReportContent](/reports/ReportContent.md) discriminated by `kind`. Provenance is
captured via [Lineage](/foundations/Lineage.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | enum | no | Content variant — `EVALUATION` \| `TEST` \| `LOG` |
| `content` | [ReportContent](/reports/ReportContent.md) | no | Content payload; the populated sub-field must match `kind`. |
| `lineage` | [Lineage](/foundations/Lineage.md) | no | Upstream artifact sources and producing operation. |
| `objectives` | set of string | no | Identifiers of the [ComplianceObjective](/objectives/ComplianceObjective.md)s this report addresses. |

## Kind values

| Value | Populated content field | Produced by |
|-------|------------------------|-------------|
| `EVALUATION` | `content.evaluation` | `DATA_PROFILING`, `MODEL_PROFILING`, `FEATURE_EVALUATION`, `RESOURCE_PROFILING` |
| `TEST` | `content.test` | `DATA_VALIDATION`, `MODEL_VALIDATION`, `DRIFT_DETECTION`, `LOG_ANALYSIS` |
| `LOG` | `content.log` | `INPUT_TRACING`, `OUTPUT_TRACING`, `RESOURCE_MONITORING` |

# Examples

```json
{
  "kind": "TEST",
  "content": {
    "test": {
      "verdict": "FAIL",
      "summary": "Equalized odds difference exceeded the 0.05 threshold.",
      "results": [
        {
          "measured": "0.083",
          "expected": { "threshold": { "operator": "LEQ", "value": 0.05 } },
          "passed": false,
          "details": "EOD computed on protected attribute 'sex' over 12 000 test samples."
        }
      ]
    }
  },
  "lineage": {
    "sources": ["dataitem::test-split-v3"],
    "operation": "run::model-validation-001"
  },
  "objectives": ["compliance-objective::eod-check-001"]
}
```
