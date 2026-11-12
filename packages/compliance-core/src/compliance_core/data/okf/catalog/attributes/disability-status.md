---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Disability Status
description: Protected characteristic under EU Charter Art. 21 and the UNCRPD. EU AI Act Art. 5 prohibits exploiting disability-related vulnerability. High-stakes fairness attribute in employment and benefits AI.
tags: ["attribute", "protected", "disability", "eu-ai-act", "eu-charter", "uncrpd"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Art. 5(1)(b); EU Charter Art. 21(1); UNCRPD Art. 5

# Instance

```json
{{
  "id": "attr-disability_status",
  "name": "Disability Status",
  "description": "Protected characteristic under EU Charter Art. 21 and the UNCRPD. EU AI Act Art. 5 prohibits exploit",
  "semantic_type": "DISABILITY",

  "attribute_role": "PROTECTED_ATTRIBUTE",
  "observability": "SELF_REPORTED",
  "use_permissions": ["FAIRNESS_TESTING", "ROBUSTNESS_SLICING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
