---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Biometric Data for Unique Identification
description: GDPR Art. 9 special category when used for unique identification. Face embeddings, fingerprints, iris scans, and voice prints are covered. Subject to EU AI Act biometric AI restrictions.
tags: ["attribute", "protected", "gdpr-art9", "biometrics", "face-recognition", "eu-ai-act"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: GDPR Art. 4(14) and 9(1); EU AI Act Art. 3(33) and Art. 5(1)(d)

# Instance

```json
{{
  "id": "attr-biometric_data",
  "name": "Biometric Data for Unique Identification",
  "description": "GDPR Art. 9 special category when used for unique identification. Face embeddings, fingerprints, iri",
  "semantic_type": "OTHER",
  "semantic_type_value": "BIOMETRIC",
  "attribute_role": "PROTECTED_ATTRIBUTE",
  "observability": "DERIVED",
  "use_permissions": ["FAIRNESS_TESTING", "RESTRICTED"]
}}
```

# Regulatory Basis

- [GDPR](../regulatory-refs/gdpr.md) — Art. 9 special categories
- [EU AI Act](../regulatory-refs/eu-ai-act.md) — Annex III and Art. 5

# Used in ComplianceContext as

- `protected_attributes` — attach to the [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — add to [DataComplianceSpec](/specs/DataComplianceSpec.md) for training/validation datasets
