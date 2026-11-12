---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Specification Container
title: DataComplianceSpec
description: Compliance extension for a data item or artifact entity, adding dataset scope, governance metadata, and attribute descriptors.
tags: [spec, data, compliance, governance, fairness, privacy]
schema: ../../okb/schemas/ComplianceSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`DataComplianceSpec` is the compliance extension for a **data item or artifact**
entity (`kind: data-compliance`, `appliesTo: ["dataitem", "artifact"]`). It extends
[ComplianceSpec](ComplianceSpec.md) with three data-specific additions:

- **`scope`** — declares whether the dataset is used for training, validation, or support
- **`governance`** — captures sensitivity, license, retention, and consent (see [DataGovernance](/data/DataGovernance.md))
- **`attributes`** — enumerates the dataset's protected/sensitive attributes for fairness and privacy auditing (see [AttributeRef](/context/AttributeRef.md))

# Schema

## Inherited from [ComplianceSpec](ComplianceSpec.md)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objectives` | set of [ComplianceObjective](/objectives/ComplianceObjective.md) | no | Normative constraints governing this dataset. |
| `compliance_status` | [ComplianceStatus](/compliance/ComplianceStatus.md) | no | Current compliance verdict. |
| `documentation` | [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) | no | Data card documentation. |

## Data-specific fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scope` | enum | no | Role of the dataset in the AI lifecycle — `TRAINING` \| `VALIDATION` \| `SUPPORT` |
| `governance` | [DataGovernance](/data/DataGovernance.md) | no | Sensitivity level, license, retention policy, and consent spec. |
| `attributes` | set of [AttributeRef](/context/AttributeRef.md) | no | Protected or sensitive attributes present in the dataset. |

# Examples

```json
{
  "scope": "TRAINING",
  "governance": {
    "sensitivity": "SENSITIVE",
    "license": "CC-BY-4.0",
    "retention": {
      "applies_to": ["TRAINING_DATA"],
      "retention_basis": "PURPOSE_NECESSITY",
      "purposes": ["TRAINING", "BIAS_DETECTION"],
      "valid_until": "2028-01-01T00:00:00Z"
    },
    "consent": {
      "consent_required": true,
      "consent_basis": "GDPR_ARTICLE_6_1_A",
      "freely_given": true,
      "specific": true,
      "informed": true
    }
  },
  "attributes": [
    {
      "id": "attr-sex", "name": "Sex",
      "semantic_type": "SEX",
      "attribute_role": "PROTECTED_ATTRIBUTE",
      "observability": "SELF_REPORTED",
      "use_permissions": ["FAIRNESS_TESTING"]
    }
  ]
}
```
