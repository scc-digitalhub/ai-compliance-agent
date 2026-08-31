---
type: AttributeRef
title: Creditworthiness Score
description: AI-derived credit score used in lending decisions. High-risk AI under EU AI Act Annex III (access to essential services). Proxy discrimination risk via postcodes, names, and spending patterns.
tags: ["attribute", "ai-derived", "credit", "financial", "eu-ai-act", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Annex III §5(b) (creditworthiness evaluation); GDPR Art. 22 (automated credit decisions)

# Instance

```json
{{
  "id": "attr-creditworthiness_score",
  "name": "Creditworthiness Score",
  "description": "AI-derived credit score used in lending decisions. High-risk AI under EU AI Act Annex III (access to",
  "semantic_type": "OTHER",
  "semantic_type_value": "CREDIT_SCORE",
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
