---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Pregnancy and Maternity Status
description: Protected under EU Directive 92/85/EEC and the Work-Life Balance Directive (2019/1158). A proxy target in recruitment and performance AI leading to indirect gender discrimination.
tags: ["attribute", "protected", "pregnancy", "maternity", "gender", "eu-directive"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU Directive 92/85/EEC; EU Directive 2019/1158; EU Charter Art. 23

# Instance

```json
{{
  "id": "attr-pregnancy_maternity",
  "name": "Pregnancy and Maternity Status",
  "description": "Protected under EU Directive 92/85/EEC and the Work-Life Balance Directive (2019/1158). A proxy targ",
  "semantic_type": "OTHER",
  "semantic_type_value": "PREGNANCY_MATERNITY",
  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "DIRECT",
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
