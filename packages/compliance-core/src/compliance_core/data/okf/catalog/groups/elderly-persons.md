---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Elderly Persons
description: Persons of advanced age who may be more susceptible to manipulation, digital exclusion, or automation bias — recognised as vulnerable under EU AI Act Art. 5.
tags: ["group", "vulnerable", "elderly", "age", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 5(1)(b) prohibits exploiting age-related vulnerability. Elderly persons may be disproportionately affected by automated credit scoring, healthcare AI, and benefit eligibility systems.

# Instance

```json
{{
  "id": "group-elderly_persons",
  "name": "Elderly Persons",
  "description": "Persons of advanced age who may be more susceptible to manipulation, digital exclusion, or automatio",
  "group_kind": "VULNERABLE",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "AGE",
  "defining_attributes": ["AttributeRef: age"],
  "rationale": "EU AI Act Art. 5(1)(b) prohibits exploiting age-related vulnerability. Elderly persons may be dispro"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
