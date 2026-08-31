---
type: Compliance Model Type
title: AttributeRef
description: Descriptor of a data attribute with semantic type, observability, and permission metadata.
tags: [context, fairness, attribute, data, privacy]
schema: ../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`AttributeRef` describes a data attribute that is either *protected* (must not be
used as a model input) or *sensitive* (restricted use). It is collected inside
[ComplianceContext](/context/ComplianceContext.md) as `protected_attributes` and
inside [GroupSpec](/context/GroupSpec.md) as `defining_attributes`.

Extends [BaseComplianceObject](/foundations/BaseComplianceObject.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | *(from BaseComplianceObject)* |
| `namespace` | string | no | *(from BaseComplianceObject)* |
| `name` | string | yes | *(from BaseComplianceObject)* |
| `description` | string | no | *(from BaseComplianceObject)* |
| `semantic_type` | enum | no | Semantic category — see below. |
| `semantic_type_value` | string | no | Free text when `semantic_type` is `OTHER`. |
| `attribute_role` | enum | no | Role in the model pipeline — see below. |
| `attribute_role_value` | string | no | Free text when `attribute_role` is `OTHER`. |
| `proxy_for` | set of AttributeRef | no | Attributes this attribute acts as a proxy for. |
| `observability` | enum | no | `DIRECT` \| `SELF_REPORTED` \| `INFERRED` \| `DERIVED` \| `PROXY` \| `EXTERNAL` \| `UNOBSERVED` \| `UNKNOWN` |
| `use_permissions` | set of enum | no | Permitted uses — see below. |

## Semantic Type Values

`AGE` · `SEX` · `GENDER` · `RACE_ETHNICITY` · `NATIONALITY` · `LANGUAGE` ·
`RELIGION` · `DISABILITY` · `HEALTH_STATUS` · `LOCATION` · `SOCIOECONOMIC_STATUS` ·
`EDUCATION` · `EMPLOYMENT_STATUS` · `OTHER`

## Attribute Role Values

`INPUT_FEATURE` · `TARGET` · `PROTECTED_ATTRIBUTE` · `SENSITIVE_ATTRIBUTE` ·
`PROXY_ATTRIBUTE` · `GROUP_ATTRIBUTE` · `STRATIFICATION_ATTRIBUTE` · `TIMESTAMP` · `OTHER`

## Use Permission Values

`MODEL_INPUT` · `TRAINING` · `EVALUATION` · `FAIRNESS_TESTING` · `ROBUSTNESS_SLICING` ·
`MONITORING` · `MITIGATION` · `REPORTING` · `EXCLUDED_FROM_MODEL` · `RESTRICTED` · `UNKNOWN`
