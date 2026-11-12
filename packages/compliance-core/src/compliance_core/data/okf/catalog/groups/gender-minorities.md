---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Gender Minorities
description: Persons whose gender identity or expression differs from the sex they were assigned at birth — protected under EU equality law and the EU Charter Art. 21.
tags: ["group", "protected", "gender", "lgbtq", "eu-charter", "fairness"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Sex life and sexual orientation are GDPR Art. 9 special categories. Gender is a protected characteristic under EU Directive 2006/54/EC. AI systems using biometric or behavioural signals risk inferring and discriminating on gender identity.

# Instance

```json
{{
  "id": "group-gender_minorities",
  "name": "Gender Minorities",
  "description": "Persons whose gender identity or expression differs from the sex they were assigned at birth — prote",
  "group_kind": "PROTECTED",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "MINORITY_STATUS",
  "defining_attributes": ["AttributeRef: gender"],
  "rationale": "Sex life and sexual orientation are GDPR Art. 9 special categories. Gender is a protected characteri"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
