---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: National Minority Membership
description: EU Charter Art. 21(1) explicitly prohibits discrimination on the ground of membership of a national minority — a protected characteristic not listed in GDPR Art. 9.
tags: ["attribute", "protected", "national-minority", "eu-charter", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU Charter Art. 21(1) (national minority membership); Framework Convention for the Protection of National Minorities (CETS 157)

# Instance

```json
{{
  "id": "attr-national_minority_membership",
  "name": "National Minority Membership",
  "description": "EU Charter Art. 21(1) explicitly prohibits discrimination on the ground of membership of a national ",
  "semantic_type": "NATIONALITY",

  "attribute_role": "PROTECTED_ATTRIBUTE",
  "observability": "SELF_REPORTED",
  "use_permissions": ["FAIRNESS_TESTING", "EXCLUDED_FROM_MODEL"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)
