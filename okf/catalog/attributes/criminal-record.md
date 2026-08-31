---
type: AttributeRef
title: Criminal Record / Conviction History
description: GDPR Art. 10 restricts processing of personal data relating to criminal convictions and offences to official authority. High risk of perpetual exclusion when used in employment, housing, or credit AI.
tags: ["attribute", "restricted", "criminal-record", "gdpr-art10", "reintegration"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 10; EU Charter Art. 49 (proportionality in criminal penalties)

# Instance

```json
{{
  "id": "attr-criminal_record",
  "name": "Criminal Record / Conviction History",
  "description": "GDPR Art. 10 restricts processing of personal data relating to criminal convictions and offences to ",
  "semantic_type": "OTHER",
  "semantic_type_value": "CRIMINAL_RECORD",
  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["FAIRNESS_TESTING", "RESTRICTED", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)
