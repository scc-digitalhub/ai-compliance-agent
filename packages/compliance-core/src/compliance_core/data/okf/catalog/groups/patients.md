---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Patients and Healthcare Recipients
description: Persons receiving medical care or health services — affected by AI systems used for diagnosis, triage, treatment recommendation, and patient prioritisation.
tags: ["group", "vulnerable", "healthcare", "patients", "medical"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Healthcare AI may produce false negatives with life-threatening consequences. Patients are frequently unable to contest or understand automated clinical decisions. EU AI Act Annex III covers AI safety components in medical devices.

# Instance

```json
{{
  "id": "group-patients",
  "name": "Patients and Healthcare Recipients",
  "description": "Persons receiving medical care or health services — affected by AI systems used for diagnosis, triag",
  "group_kind": "VULNERABLE",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "HEALTH_STATUS",
  "defining_attributes": ["AttributeRef: health_status"],
  "rationale": "Healthcare AI may produce false negatives with life-threatening consequences. Patients are frequentl"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
