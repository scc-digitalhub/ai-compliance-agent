---
type: AttributeRef
title: Health / Life Insurance Risk Score
description: AI-derived actuarial risk score used in health or life insurance pricing. High-risk under EU AI Act Annex III. May constitute indirect discrimination based on health status or disability.
tags: ["attribute", "ai-derived", "insurance", "actuarial", "health", "eu-ai-act", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Annex III §5(d) (insurance AI); GDPR Art. 9 (health data basis); EU Gender Goods and Services Directive 2004/113/EC

# Instance

```json
{{
  "id": "attr-insurance_risk_score",
  "name": "Health / Life Insurance Risk Score",
  "description": "AI-derived actuarial risk score used in health or life insurance pricing. High-risk under EU AI Act ",
  "semantic_type": "OTHER",
  "semantic_type_value": "INSURANCE_RISK",
  "attribute_role": "TARGET",
  "observability": "DERIVED",
  "use_permissions": ["EVALUATION", "FAIRNESS_TESTING", "ROBUSTNESS_SLICING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)
