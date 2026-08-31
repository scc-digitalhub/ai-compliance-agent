---
type: AttributeRef
title: Genetic Data
description: GDPR Art. 9 special category. Unique to an individual, immutable, and predictive of future health conditions. High risk in insurance and employment AI.
tags: ["attribute", "protected", "gdpr-art9", "genetic", "dna"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 4(13) and 9(1); Directive 98/44/EC

# Instance

```json
{{
  "id": "attr-genetic_data",
  "name": "Genetic Data",
  "description": "GDPR Art. 9 special category. Unique to an individual, immutable, and predictive of future health co",
  "semantic_type": "HEALTH_STATUS",

  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL", "RESTRICTED"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
