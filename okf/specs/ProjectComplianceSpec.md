---
type: Compliance Specification Container
title: ProjectComplianceSpec
description: Compliance extension for a project entity, adding AI-task classification, domain, deployment kind, audience, scope, and the active compliance context.
tags: [spec, project, compliance, context, domain]
schema: ../../okb/schemas/ComplianceSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ProjectComplianceSpec` is the compliance extension for a **project** entity
(`kind: ai-compliance`, `appliesTo: ["project"]`). It extends
[ComplianceSpec](ComplianceSpec.md) with project-specific fields that
describe *what* the AI application does, *for whom*, and *in which deployment context*.

The [ComplianceContext](/context/ComplianceContext.md) field is the primary anchor
for regulations, risk classification, oversight profile, misuse scenarios, and
requirements scoped to this project's deployment.

# Schema

## Inherited from [ComplianceSpec](ComplianceSpec.md)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objectives` | set of [ComplianceObjective](/objectives/ComplianceObjective.md) | no | Normative constraints governing this project. |
| `compliance_status` | [ComplianceStatus](/compliance/ComplianceStatus.md) | no | Current compliance verdict. |
| `documentation` | [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) | no | Structured compliance documentation. |

## Project-specific fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | [DomainDescriptor](/foundations/DomainDescriptor.md) | yes | Application domain, subdomain, and use-case. |
| `ai_task` | enum | yes | Primary AI task type — see below. |
| `ai_task_value` | string | no | Free text when `ai_task` is `OTHER`. |
| `goal` | string | yes | High-level goal of the AI application. |
| `purpose` | string | no | Intended function or business capability. |
| `audience` | string | no | Target users — e.g. `internal analysts`, `end consumers`. |
| `scope` | [ProjectScope](#projectscope) | no | In-scope and out-of-scope capabilities. |
| `deployment` | enum | no | `EDGE` \| `PREMISE` \| `CLOUD` \| `EMBEDDED` |
| `context` | [ComplianceContext](/context/ComplianceContext.md) | no | Active deployment context (regulations, risk, oversight). |

## AiTask Values

`CLASSIFICATION` · `REGRESSION` · `RANKING` · `RECOMMENDATION` · `GENERATION` ·
`DETECTION` · `FORECASTING` · `CONTROL` · `DECISION_SUPPORT` · `OTHER`

## ProjectScope

| Field | Type | Description |
|-------|------|-------------|
| `in_scope` | list of string | Capabilities / functions included in the project. |
| `out_of_scope` | list of string | Explicitly excluded capabilities. |

# Examples

```json
{
  "domain": { "domain": "healthcare", "subdomain": "radiology", "use_case": "Tumour detection" },
  "ai_task": "DETECTION",
  "goal": "Automate preliminary screening of CT scans to flag suspicious regions.",
  "purpose": "Clinical decision support for radiologists.",
  "audience": "Certified radiologists in partner hospitals.",
  "deployment": "CLOUD",
  "scope": {
    "in_scope":     ["CT scan analysis", "anomaly flagging"],
    "out_of_scope": ["Final diagnosis", "Treatment planning"]
  },
  "objectives": [],
  "compliance_status": null
}
```
