---
type: AttributeRef
title: Socioeconomic Status
description: Proxy for multiple protected characteristics. EU AI Act Art. 5 prohibits exploiting socioeconomic vulnerability. High fairness risk in credit, benefits, and employment AI.
tags: ["attribute", "protected", "socioeconomic", "poverty", "proxy", "eu-ai-act"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Art. 5(1)(b); EU Charter Art. 21(1) (social origin)

# Instance

```json
{{
  "id": "attr-socioeconomic_status",
  "name": "Socioeconomic Status",
  "description": "Proxy for multiple protected characteristics. EU AI Act Art. 5 prohibits exploiting socioeconomic vu",
  "semantic_type": "SOCIOECONOMIC_STATUS",

  "attribute_role": "PROXY_ATTRIBUTE",
  "observability": "DERIVED",
  "use_permissions": ["FAIRNESS_TESTING", "ROBUSTNESS_SLICING"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
