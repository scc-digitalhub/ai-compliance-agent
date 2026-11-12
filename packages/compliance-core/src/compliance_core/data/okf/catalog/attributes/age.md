---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Age
description: Protected characteristic under EU AI Act Art. 5 (exploitation of age-related vulnerabilities) and GDPR Art. 8 (children's consent threshold). Proxy for protected groups in many domains.
tags: ["attribute", "protected", "age", "eu-ai-act", "gdpr"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Art. 5(1)(b); GDPR Art. 8; EU Charter Art. 21(1)

# Instance

```json
{{
  "id": "attr-age",
  "name": "Age",
  "description": "Protected characteristic under EU AI Act Art. 5 (exploitation of age-related vulnerabilities) and GD",
  "semantic_type": "AGE",

  "attribute_role": "STRATIFICATION_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["MODEL_INPUT", "FAIRNESS_TESTING", "ROBUSTNESS_SLICING"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
