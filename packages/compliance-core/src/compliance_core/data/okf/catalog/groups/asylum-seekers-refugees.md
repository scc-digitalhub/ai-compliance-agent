---
type: GroupSpec
title: Asylum Seekers and Refugees
description: Persons seeking international protection or who have been granted refugee status — subject to specific high-risk AI applications under EU AI Act Annex III (migration, asylum, border control).
tags: ["group", "vulnerable", "asylum", "refugee", "migration", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Annex III lists migration, asylum and border control AI as high-risk. Asylum seekers face high-stakes automated decisions on visa and residence applications.

# Instance

```json
{{
  "id": "group-asylum_seekers_refugees",
  "name": "Asylum Seekers and Refugees",
  "description": "Persons seeking international protection or who have been granted refugee status — subject to specif",
  "group_kind": "VULNERABLE",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "MINORITY_STATUS",
  "defining_attributes": ["AttributeRef: nationality", "AttributeRef: language"],
  "rationale": "EU AI Act Annex III lists migration, asylum and border control AI as high-risk. Asylum seekers face "
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
