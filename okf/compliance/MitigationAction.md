---
type: Compliance Model Type
title: MitigationAction
description: Action engaged to resolve a compliance objective violation, with lifecycle status, owner, evidence, and residual risk assessment.
tags: [compliance, mitigation, remediation, risk, action]
schema: ../okb/schemas/MitigationAction.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`MitigationAction` tracks the lifecycle of a remediation effort in response to a
[ComplianceFinding](/compliance/ComplianceFinding.md). It is collected in
[ComplianceStatus](/compliance/ComplianceStatus.md) as `mitigations`. Evidence
artefacts are referenced via [EntityRef](/foundations/EntityRef.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | Action lifecycle state — see below. |
| `rationale` | string | no | Why this action was chosen. |
| `owner` | [ActorRef](/foundations/ActorRef.md) | no | Responsible party. |
| `due_at` | datetime | no | Target completion date. |
| `applied_at` | datetime | no | When the action was applied. |
| `evidence` | set of [EntityRef](/foundations/EntityRef.md) | no | References to supporting evidence artefacts. |
| `verification_report` | [EntityRef](/foundations/EntityRef.md) | no | Report confirming the action resolved the violation. |
| `residual_status` | enum | no | Status of residual risk after action — see below. |

## Status Values

`NOT_REQUIRED` · `PROPOSED` · `PLANNED` · `IN_PROGRESS` · `APPLIED` · `VERIFIED` ·
`REJECTED` · `DEFERRED` · `ACCEPTED_RISK`

## Residual Status Values

`OPEN` · `PARTIALLY_RESOLVED` · `RESOLVED` · `UNRESOLVED` ·
`ACCEPTED_RESIDUAL_RISK` · `NEEDS_RETEST`
