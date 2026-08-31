---
type: AttributeRef
title: Racial / Ethnic Origin
description: GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d) biometric categorisation ban.
tags: ["attribute", "protected", "gdpr-art9", "race", "ethnicity", "eu-ai-act"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1); EU Charter Art. 21(1); EU AI Act Art. 5(1)(d)

# Instance

```json
{{
  "id": "attr-racial_ethnic_origin",
  "name": "Racial / Ethnic Origin",
  "description": "GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d) biometric cat",
  "semantic_type": "RACE_ETHNICITY",

  "attribute_role": "PROTECTED_ATTRIBUTE",
  "observability": "INFERRED",
  "use_permissions": ["FAIRNESS_TESTING", "ROBUSTNESS_SLICING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
