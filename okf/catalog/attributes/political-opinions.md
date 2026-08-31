---
type: AttributeRef
title: Political Opinions
description: GDPR Art. 9 special category. High risk of discriminatory use in content moderation, hiring, and law enforcement AI.
tags: ["attribute", "protected", "gdpr-art9", "politics", "opinion"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1); EU Charter Art. 11 (freedom of expression)

# Instance

```json
{{
  "id": "attr-political_opinions",
  "name": "Political Opinions",
  "description": "GDPR Art. 9 special category. High risk of discriminatory use in content moderation, hiring, and law",
  "semantic_type": "OTHER",
  "semantic_type_value": "POLITICAL_OPINION",
  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "INFERRED",
  "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
