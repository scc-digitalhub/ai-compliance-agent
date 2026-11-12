---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Sex Life and Sexual Orientation
description: GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d). Particular risk in behavioural AI, recommendation engines, and social platforms.
tags: ["attribute", "protected", "gdpr-art9", "sexual-orientation", "lgbtq"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1); EU Charter Art. 21(1)

# Instance

```json
{{
  "id": "attr-sex_life_sexual_orientation",
  "name": "Sex Life and Sexual Orientation",
  "description": "GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d). Particular r",
  "semantic_type": "OTHER",
  "semantic_type_value": "SEXUAL_ORIENTATION",
  "attribute_role": "PROTECTED_ATTRIBUTE",
  "observability": "INFERRED",
  "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
