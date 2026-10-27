---
type: GroupSpec
title: Students
description: Persons enrolled in educational or vocational training institutions — subject to high-risk AI under EU AI Act Annex III (education and vocational training).
tags: ["group", "occupational", "education", "students", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Annex III classifies AI determining access to educational institutions and evaluating learning outcomes as high-risk. Students may face automated exclusion from education based on opaque AI decisions.

# Instance

```json
{{
  "id": "group-students",
  "name": "Students",
  "description": "Persons enrolled in educational or vocational training institutions — subject to high-risk AI under ",
  "group_kind": "USER_GROUP",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "EDUCATIONAL_ACCESS",
  "defining_attributes": ["AttributeRef: age", "AttributeRef: education"],
  "rationale": "EU AI Act Annex III classifies AI determining access to educational institutions and evaluating lear"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
