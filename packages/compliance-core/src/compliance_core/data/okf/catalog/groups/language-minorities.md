---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: National Language Minorities
description: Persons belonging to national or linguistic minorities — explicitly protected under EU Charter Art. 21(1) and Art. 22; at risk of exclusion from AI systems optimised for majority languages.
tags: ["group", "protected", "language", "national-minority", "eu-charter", "digital-exclusion"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU Charter Art. 21(1) explicitly lists membership of a national minority and language as prohibited discrimination grounds. NLP and voice AI systems trained on majority-language data systematically underperform for linguistic minorities.

# Instance

```json
{{
  "id": "group-language_minorities",
  "name": "National Language Minorities",
  "description": "Persons belonging to national or linguistic minorities — explicitly protected under EU Charter Art. ",
  "group_kind": "LANGUAGE_GROUP",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "LANGUAGE_ACCESS",
  "defining_attributes": ["AttributeRef: nationality", "AttributeRef: language"],
  "rationale": "EU Charter Art. 21(1) explicitly lists membership of a national minority and language as prohibited "
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` or `vulnerable_groups`
