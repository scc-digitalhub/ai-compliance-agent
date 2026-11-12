---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Affected Persons (Non-users)
description: Natural persons who are subject to decisions or outputs of an AI system without directly interacting with it — e.g. persons assessed by credit scoring or predictive policing AI.
tags: ["group", "affected", "non-user", "eu-ai-act", "decision-subject"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 4(5) defines affected persons separately from deployers and end users. GDPR Art. 22 protects affected persons from purely automated significant decisions. High-risk AI Annex III use cases mostly concern affected persons, not voluntary users.

# Instance

```json
{{
  "id": "group-affected_persons",
  "name": "Affected Persons (Non-users)",
  "description": "Natural persons who are subject to decisions or outputs of an AI system without directly interacting",
  "group_kind": "DEMOGRAPHIC",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": null,
  "defining_attributes": [],
  "rationale": "EU AI Act Art. 4(5) defines affected persons separately from deployers and end users. GDPR Art. 22 p"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
