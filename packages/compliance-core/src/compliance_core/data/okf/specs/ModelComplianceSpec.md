---
type: Compliance Specification Container
title: ModelComplianceSpec
description: Compliance extension for a model entity, inheriting all ComplianceSpec fields with no additional model-specific properties.
tags: [spec, model, compliance]
schema: ../../okb/schemas/ComplianceSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ModelComplianceSpec` is the compliance extension for a **model** entity
(`kind: model-compliance`, `appliesTo: ["model"]`). It extends
[ComplianceSpec](ComplianceSpec.md) without adding model-specific fields;
the inherited spec fields are sufficient to track objectives, status, findings,
and documentation for a model artifact.

Compliance objectives attached here typically address:
- **Performance** — accuracy, F1, AUC benchmarks
- **Fairness** — equalized odds, demographic parity differences
- **Robustness** — adversarial accuracy, out-of-distribution performance
- **Transparency** — interpretability scores, feature attribution coverage

# Schema

## Inherited from [ComplianceSpec](ComplianceSpec.md)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objectives` | set of [ComplianceObjective](/objectives/ComplianceObjective.md) | no | Normative constraints governing this model. |
| `compliance_status` | [ComplianceStatus](/compliance/ComplianceStatus.md) | no | Current compliance verdict. |
| `documentation` | [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) | no | Model card documentation. |

*No additional fields beyond the inherited ones.*

# Examples

```json
{
  "objectives": [
    {
      "name": "Equalized Odds Difference <= 0.05",
      "metric": { "id": "eod", "name": "Equalized Odds Difference", "kind": "PRIMITIVE", "scale": "RATIO" },
      "condition": { "threshold": { "operator": "LEQ", "value": 0.05 } },
      "priority": "MANDATORY",
      "severity": "HIGH",
      "requirements": ["req-eu-ai-art10"]
    }
  ],
  "compliance_status": {
    "status": "COMPLIANT",
    "assessed_at": "2026-08-01T09:00:00Z",
    "assessor": { "kind": "HUMAN", "id": "alice@example.com" }
  }
}
```
