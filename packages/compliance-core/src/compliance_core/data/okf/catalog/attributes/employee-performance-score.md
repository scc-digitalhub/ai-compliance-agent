---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Employee Performance Score
description: AI-derived performance or productivity score used in HR decisions (promotion, termination, task allocation). High-risk under EU AI Act Annex III. Covered by EU Platform Work Directive for gig workers.
tags: ["attribute", "ai-derived", "employment", "hr", "performance", "eu-ai-act", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU AI Act Annex III §4 (employment AI); EU Platform Work Directive (2024); GDPR Art. 22

# Instance

```json
{{
  "id": "attr-employee_performance_score",
  "name": "Employee Performance Score",
  "description": "AI-derived performance or productivity score used in HR decisions (promotion, termination, task allo",
  "semantic_type": "OTHER",
  "semantic_type_value": "EMPLOYEE_PERFORMANCE",
  "attribute_role": "TARGET",
  "observability": "DERIVED",
  "use_permissions": ["EVALUATION", "FAIRNESS_TESTING", "ROBUSTNESS_SLICING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)
