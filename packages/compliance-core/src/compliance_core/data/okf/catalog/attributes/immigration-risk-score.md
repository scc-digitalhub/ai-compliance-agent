---
type: AttributeRef
title: Immigration / Border Risk Score
description: AI-derived risk classification used in visa, asylum, or border control decisions. High-risk under EU AI Act Annex III. Particular fairness risk for asylum seekers and refugees.
tags: ["attribute", "ai-derived", "immigration", "border", "asylum", "eu-ai-act", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Annex III §7 (migration AI); EU Charter Art. 18 (right to asylum); GDPR Art. 9 (biometric data of asylum seekers)

# Instance

```json
{{
  "id": "attr-immigration_risk_score",
  "name": "Immigration / Border Risk Score",
  "description": "AI-derived risk classification used in visa, asylum, or border control decisions. High-risk under EU",
  "semantic_type": "OTHER",
  "semantic_type_value": "IMMIGRATION_RISK",
  "attribute_role": "TARGET",
  "observability": "DERIVED",
  "use_permissions": ["EVALUATION", "FAIRNESS_TESTING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)
