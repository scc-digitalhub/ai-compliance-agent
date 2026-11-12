---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Persons with Low Digital Literacy
description: Persons lacking the skills to critically engage with digital systems and AI outputs — at heightened risk of automation bias, manipulation, and inability to exercise rights against AI decisions.
tags: ["group", "vulnerable", "digital-literacy", "exclusion", "capacity"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

UNESCO AI Ethics Recommendation (§4.6) and the EU AI Act Art. 13 (instructions for use) implicitly require that AI systems be usable by persons of varying digital literacy. Persons with low digital literacy cannot meaningfully exercise their rights under GDPR Art. 22 or contest AI decisions.

# Instance

```json
{{
  "id": "group-persons_without_digital_literacy",
  "name": "Persons with Low Digital Literacy",
  "description": "Persons lacking the skills to critically engage with digital systems and AI outputs — at heightened ",
  "group_kind": "VULNERABLE",
  "group_role": "END_USER",
  "vulnerability": "DIGITAL_LITERACY",
  "defining_attributes": ["AttributeRef: age", "AttributeRef: education"],
  "rationale": "UNESCO AI Ethics Recommendation (§4.6) and the EU AI Act Art. 13 (instructions for use) implicitly r"
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` or `vulnerable_groups`
