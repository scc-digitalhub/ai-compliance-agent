---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Economically Disadvantaged Persons
description: Persons in situations of financial hardship or socio-economic dependency, identified in EU AI Act Art. 5 as a group whose vulnerabilities must not be exploited.
tags: ["group", "vulnerable", "socioeconomic", "poverty", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 5(1)(b) prohibits AI systems exploiting socio-economic circumstances. Economically disadvantaged persons are disproportionately affected by credit, benefits, and employment AI systems.

# Instance

```json
{{
  "id": "group-economically_disadvantaged",
  "name": "Economically Disadvantaged Persons",
  "description": "Persons in situations of financial hardship or socio-economic dependency, identified in EU AI Act Ar",
  "group_kind": "VULNERABLE",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "ECONOMIC_DEPENDENCY",
  "defining_attributes": ["AttributeRef: socioeconomic_status"],
  "rationale": "EU AI Act Art. 5(1)(b) prohibits AI systems exploiting socio-economic circumstances. Economically di"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
