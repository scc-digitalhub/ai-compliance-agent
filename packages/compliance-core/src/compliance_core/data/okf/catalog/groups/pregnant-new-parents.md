---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Pregnant Women and New Parents
description: Persons who are pregnant or in the parental period — protected under EU Directive 92/85/EEC and Directive 2019/1158; at risk from employment AI that treats pregnancy as a negative signal.
tags: ["group", "protected", "pregnancy", "maternity", "parental", "gender-equality", "eu-directive"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU Directive 92/85/EEC and the Work-Life Balance Directive (2019/1158) protect pregnant workers. Recruitment and performance AI that penalises absences or career breaks effectively discriminates against persons exercising parental rights.

# Instance

```json
{{
  "id": "group-pregnant_new_parents",
  "name": "Pregnant Women and New Parents",
  "description": "Persons who are pregnant or in the parental period — protected under EU Directive 92/85/EEC and Dire",
  "group_kind": "PROTECTED",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "HEALTH_STATUS",
  "defining_attributes": ["AttributeRef: gender"],
  "rationale": "EU Directive 92/85/EEC and the Work-Life Balance Directive (2019/1158) protect pregnant workers. Rec"
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` or `vulnerable_groups`
