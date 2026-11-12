---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Gender
description: Protected characteristic under EU Directive 2006/54/EC. High fairness risk in hiring, credit, and healthcare AI. Distinct from sex life/sexual orientation but often conflated.
tags: ["attribute", "protected", "gender", "sex", "eu-directive", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU Directive 2006/54/EC; EU Charter Art. 23 (equality between women and men)

# Instance

```json
{{
  "id": "attr-gender",
  "name": "Gender",
  "description": "Protected characteristic under EU Directive 2006/54/EC. High fairness risk in hiring, credit, and he",
  "semantic_type": "GENDER",

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
