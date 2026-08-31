---
type: GroupSpec
title: Racial and Ethnic Minorities
description: Groups defined by racial or ethnic origin — a GDPR Art. 9 special category and a protected characteristic under EU law subject to non-discrimination requirements.
tags: ["group", "protected", "race", "ethnicity", "gdpr", "fairness"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Racial and ethnic origin is a GDPR Art. 9 special category. EU AI Act Annex III requires bias examination in training data with respect to protected characteristics. Facial recognition and predictive policing AI have documented racial disparities.

# Instance

```json
{{
  "id": "group-racial_ethnic_minorities",
  "name": "Racial and Ethnic Minorities",
  "description": "Groups defined by racial or ethnic origin — a GDPR Art. 9 special category and a protected character",
  "group_kind": "PROTECTED",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "MINORITY_STATUS",
  "defining_attributes": ["AttributeRef: race_ethnicity"],
  "rationale": "Racial and ethnic origin is a GDPR Art. 9 special category. EU AI Act Annex III requires bias examin"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
