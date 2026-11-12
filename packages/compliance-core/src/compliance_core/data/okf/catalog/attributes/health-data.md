---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Health Data
description: GDPR Art. 9 special category. Core input/output in healthcare AI. Processing requires explicit consent or a specific Art. 9(2) exemption.
tags: ["attribute", "protected", "gdpr-art9", "health", "medical"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 9(1)(h); EU AI Act Annex I (medical devices)

# Instance

```json
{{
  "id": "attr-health_data",
  "name": "Health Data",
  "description": "GDPR Art. 9 special category. Core input/output in healthcare AI. Processing requires explicit conse",
  "semantic_type": "HEALTH_STATUS",

  "attribute_role": "SENSITIVE_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["MODEL_INPUT", "TRAINING", "FAIRNESS_TESTING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
