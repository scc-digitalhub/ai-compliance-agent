---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Nationality
description: Proxy for race/ethnicity. Relevant in migration AI (EU AI Act Annex III) and credit/employment AI. May correlate with language access barriers.
tags: ["attribute", "protected", "nationality", "migration", "proxy", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU Charter Art. 21(2) (non-discrimination on grounds of nationality); EU AI Act Annex III (migration AI)

# Instance

```json
{{
  "id": "attr-nationality",
  "name": "Nationality",
  "description": "Proxy for race/ethnicity. Relevant in migration AI (EU AI Act Annex III) and credit/employment AI. M",
  "semantic_type": "NATIONALITY",

  "attribute_role": "PROXY_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["FAIRNESS_TESTING", "ROBUSTNESS_SLICING"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
