---
type: AttributeRef
title: Criminal Recidivism Risk Score
description: AI-derived risk score estimating the probability that a person will re-offend. High-risk AI under EU AI Act Annex III (law enforcement). Documented racial and socioeconomic disparities (e.g. COMPAS).
tags: ["attribute", "ai-derived", "law-enforcement", "recidivism", "eu-ai-act", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Annex III §6 (law enforcement); GDPR Art. 10 (criminal convictions data)

# Instance

```json
{{
  "id": "attr-recidivism_risk_score",
  "name": "Criminal Recidivism Risk Score",
  "description": "AI-derived risk score estimating the probability that a person will re-offend. High-risk AI under EU",
  "semantic_type": "OTHER",
  "semantic_type_value": "RECIDIVISM_RISK",
  "attribute_role": "TARGET",
  "observability": "DERIVED",
  "use_permissions": ["EVALUATION", "FAIRNESS_TESTING", "ROBUSTNESS_SLICING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
