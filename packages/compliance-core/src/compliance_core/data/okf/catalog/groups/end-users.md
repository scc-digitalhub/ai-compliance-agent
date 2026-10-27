---
type: GroupSpec
title: End Users
description: Natural persons who directly interact with an AI system's output in their personal capacity — not to be confused with deployers (professional users).
tags: ["group", "user-group", "end-user", "consumer"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 50 grants end users the right to know they are interacting with AI (chatbot disclosure). GDPR Art. 22 grants end users rights when subject to automated decisions.

# Instance

```json
{{
  "id": "group-end_users",
  "name": "End Users",
  "description": "Natural persons who directly interact with an AI system's output in their personal capacity — not to",
  "group_kind": "USER_GROUP",
  "group_role": "END_USER",
  "vulnerability": null,
  "defining_attributes": [],
  "rationale": "EU AI Act Art. 50 grants end users the right to know they are interacting with AI (chatbot disclosur"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
