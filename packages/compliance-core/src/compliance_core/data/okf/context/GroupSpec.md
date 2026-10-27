---
type: Compliance Model Type
title: GroupSpec
description: Specification of a population group relevant to a compliance context, including vulnerability and defining attributes.
tags: [context, fairness, population, group, vulnerability]
schema: ../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`GroupSpec` describes a cohort of people with respect to a compliance concern:
who they are (`group_kind`), their relationship to the system (`group_role`),
which [attributes](/context/AttributeRef.md) define membership, and whether the
group is considered vulnerable.

It is collected in [ComplianceContext](/context/ComplianceContext.md)
(`affected_groups`, `vulnerable_groups`) and [MisuseScenario](/context/MisuseScenario.md)
(`affected_groups`).

Extends [BaseComplianceObject](/foundations/BaseComplianceObject.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | *(from BaseComplianceObject)* |
| `namespace` | string | no | *(from BaseComplianceObject)* |
| `name` | string | yes | *(from BaseComplianceObject)* |
| `description` | string | no | *(from BaseComplianceObject)* |
| `group_kind` | enum | no | Category of the group — see below. |
| `group_kind_value` | string | no | Free text when `group_kind` is `OTHER`. |
| `group_role` | enum | no | Relationship to the AI system — see below. |
| `group_role_value` | string | no | Free text when `group_role` is `OTHER`. |
| `defining_attributes` | set of [AttributeRef](/context/AttributeRef.md) | no | Attributes that characterise group membership. |
| `vulnerability` | enum | no | Vulnerability dimension — see below. |
| `vulnerability_value` | string | no | Free text when `vulnerability` is `OTHER`. |
| `rationale` | string | no | Justification for including this group. |

## Group Kind Values

`DEMOGRAPHIC` · `PROTECTED` · `VULNERABLE` · `OCCUPATIONAL` · `USER_GROUP` ·
`GEOGRAPHIC` · `LANGUAGE_GROUP` · `SOCIOECONOMIC` · `TECHNICAL_ENVIRONMENT` · `OTHER`

## Group Role Values

`TARGET_SUBJECT` · `DECISION_SUBJECT` · `END_USER` · `OPERATOR` ·
`BENEFICIARY` · `EXCLUDED_POPULATION` · `REFERENCE_GROUP` · `OTHER`

## Vulnerability Values

`AGE` · `DISABILITY` · `HEALTH_STATUS` · `ECONOMIC_DEPENDENCY` · `EDUCATIONAL_ACCESS` ·
`DIGITAL_LITERACY` · `EMPLOYMENT_DEPENDENCY` · `MINORITY_STATUS` · `LANGUAGE_ACCESS` · `OTHER`
