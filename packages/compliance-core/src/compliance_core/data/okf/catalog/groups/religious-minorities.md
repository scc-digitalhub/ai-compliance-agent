---
type: GroupSpec
title: Religious Minorities
description: Groups defined by religious or philosophical beliefs — a GDPR Art. 9 special category and protected under EU Charter Art. 10 (freedom of religion).
tags: ["group", "protected", "religion", "gdpr", "eu-charter"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Religious beliefs are a GDPR Art. 9 special category and an EU AI Act prohibited inference target (Art. 5 biometric categorisation ban). Religious minorities face risks from profiling, surveillance, and benefits AI.

# Instance

```json
{{
  "id": "group-religious_minorities",
  "name": "Religious Minorities",
  "description": "Groups defined by religious or philosophical beliefs — a GDPR Art. 9 special category and protected ",
  "group_kind": "PROTECTED",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "MINORITY_STATUS",
  "defining_attributes": ["AttributeRef: religion"],
  "rationale": "Religious beliefs are a GDPR Art. 9 special category and an EU AI Act prohibited inference target (A"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
