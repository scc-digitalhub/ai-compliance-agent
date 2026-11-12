---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Religious or Philosophical Beliefs
description: GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d). High risk in content moderation and social scoring AI.
tags: ["attribute", "protected", "gdpr-art9", "religion", "philosophy"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1); EU Charter Art. 10 (freedom of religion)

# Instance

```json
{{
  "id": "attr-religious_beliefs",
  "name": "Religious or Philosophical Beliefs",
  "description": "GDPR Art. 9 special category. Prohibited inference target under EU AI Act Art. 5(1)(d). High risk in",
  "semantic_type": "RELIGION",

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
