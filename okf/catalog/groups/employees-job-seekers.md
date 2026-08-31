---
type: GroupSpec
title: Employees and Job Seekers
description: Persons in employment relationships or seeking employment — subject to high-risk AI under EU AI Act Annex III (employment, workers management, access to self-employment).
tags: ["group", "occupational", "employment", "recruitment", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Annex III classifies recruitment AI (job ads, CV screening, interview tools) and performance monitoring AI as high-risk. Employees are subject to decisions with significant impact on their livelihoods.

# Instance

```json
{{
  "id": "group-employees_job_seekers",
  "name": "Employees and Job Seekers",
  "description": "Persons in employment relationships or seeking employment — subject to high-risk AI under EU AI Act ",
  "group_kind": "OCCUPATIONAL",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "EMPLOYMENT_DEPENDENCY",
  "defining_attributes": ["AttributeRef: employment_status"],
  "rationale": "EU AI Act Annex III classifies recruitment AI (job ads, CV screening, interview tools) and performan"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
