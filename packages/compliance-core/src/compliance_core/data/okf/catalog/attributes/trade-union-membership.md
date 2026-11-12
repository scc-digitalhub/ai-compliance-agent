---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Trade Union Membership
description: GDPR Art. 9 special category. Processing by employment AI systems carries risk of unlawful labour discrimination.
tags: ["attribute", "protected", "gdpr-art9", "trade-union", "employment"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1); EU Charter Art. 12 (freedom of association)

# Instance

```json
{{
  "id": "attr-trade_union_membership",
  "name": "Trade Union Membership",
  "description": "GDPR Art. 9 special category. Processing by employment AI systems carries risk of unlawful labour di",
  "semantic_type": "OTHER",
  "semantic_type_value": "TRADE_UNION_MEMBERSHIP",
  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "SELF_REPORTED",
  "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
