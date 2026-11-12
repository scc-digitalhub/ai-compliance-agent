---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Persons with Disabilities
description: Persons with physical, mental, intellectual, or sensory impairments that in interaction with barriers may hinder full participation — a protected group under EU AI Act and UNCRPD.
tags: ["group", "vulnerable", "disability", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 5(1)(b) explicitly prohibits exploiting disabilities as a vulnerability. Disability status is a protected characteristic under the EU Charter of Fundamental Rights Art. 21.

# Instance

```json
{{
  "id": "group-persons_with_disabilities",
  "name": "Persons with Disabilities",
  "description": "Persons with physical, mental, intellectual, or sensory impairments that in interaction with barrier",
  "group_kind": "VULNERABLE",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "DISABILITY",
  "defining_attributes": ["AttributeRef: disability_status"],
  "rationale": "EU AI Act Art. 5(1)(b) explicitly prohibits exploiting disabilities as a vulnerability. Disability s"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
