---
type: Compliance Requirement
title: Requirement
description: A normative compliance requirement derived from a regulatory framework, with applicability status and traceability.
tags: [context, requirement, regulation, traceability]
schema: ../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`Requirement` captures a single obligation from a [regulatory framework](/foundations/RegulatoryRef.md),
its classification kind, and its applicability in the deployment context.
Requirements are collected inside a [ComplianceContext](/context/ComplianceContext.md)
and referenced by [ComplianceObjective](/objectives/ComplianceObjective.md) via
string identifiers.

Extends [BaseComplianceObject](/foundations/BaseComplianceObject.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | *(from BaseComplianceObject)* Locally unique identifier. |
| `namespace` | string | no | *(from BaseComplianceObject)* Scoping context. |
| `name` | string | yes | *(from BaseComplianceObject)* Short requirement name. |
| `description` | string | no | *(from BaseComplianceObject)* Free-text summary. |
| `source` | [RegulatoryRef](/foundations/RegulatoryRef.md) | yes | Normative source of this requirement. |
| `requirement_text` | string | yes | Full verbatim text of the requirement. |
| `summary` | string | no | Short paraphrase for display. |
| `kind` | enum | yes | Requirement category — see below. |
| `applicability_status` | enum | yes | `APPLICABLE` \| `NOT_APPLICABLE` \| `PARTIALLY_APPLICABLE` \| `UNCERTAIN` \| `NEEDS_REVIEW` |
| `related_requirements` | set of string | no | Identifiers of related requirements. |

## Kind Values

`DESIGN` · `TESTING` · `DOCUMENTATION` · `MONITORING` · `DATA_PROTECTION` ·
`TRANSPARENCY` · `HUMAN_OVERSIGHT` · `DATA_GOVERNANCE` · `RISK_MANAGEMENT` ·
`CYBERSECURITY` · `QUALITY_MANAGEMENT` · `OPERATIONAL_CONTROL` · `OTHER`
