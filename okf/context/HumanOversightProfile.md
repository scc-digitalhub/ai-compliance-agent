---
type: Compliance Model Type
title: HumanOversightProfile
description: Profile describing the human oversight mode, authority, intervention points, and escalation channels for an AI deployment.
tags: [context, oversight, human-in-the-loop, governance, eu-ai-act]
schema: ../okb/schemas/HumanOversightProfile.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`HumanOversightProfile` records how human oversight is implemented for a specific
deployment context. It maps directly onto the Article 14 requirements of the EU AI
Act and is embedded in [ComplianceContext](/context/ComplianceContext.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oversight_mode` | enum | yes | Primary oversight posture — see below. |
| `oversight_mode_value` | string | no | Free text when `oversight_mode` is `OTHER`. |
| `overseer_roles` | set of ActorRole | yes | Roles responsible for oversight. |
| `intervention_points` | set of enum | no | Lifecycle gates where humans may intervene — see below. |
| `authority` | set of enum | no | Powers granted to overseers — see below. |
| `availability` | enum | no | `CONTINUOUS` \| `BUSINESS_HOURS` \| `ON_CALL` \| `BATCH_REVIEW` \| `PERIODIC` \| `NONE` |
| `escalation_channels` | set of enum | no | Escalation paths — see below. |
| `limitations` | set of string | no | Known constraints on oversight effectiveness. |
| `rationale` | string | no | Justification for the chosen oversight mode. |

## Oversight Mode Values

`HUMAN_IN_THE_LOOP` · `HUMAN_IN_COMMAND` · `PRE_DEPLOYMENT_APPROVAL` ·
`POST_HOC_REVIEW` · `EXCEPTION_BASED_REVIEW` · `FULLY_AUTOMATED_WITH_ESCALATION` ·
`MANUAL_OPERATION` · `NONE` · `OTHER`

## Intervention Point Values

`DATA_APPROVAL` · `TRAINING_APPROVAL` · `TEST_APPROVAL` · `THRESHOLD_APPROVAL` ·
`DEPLOYMENT_APPROVAL` · `INPUT_REVIEW` · `OUTPUT_REVIEW` · `DECISION_APPROVAL` ·
`ABSTENTION_REVIEW` · `ESCALATION_REVIEW` · `INCIDENT_REVIEW` · `OTHER`

## Authority Values

`VIEW_ONLY` · `REQUEST_EXPLANATION` · `APPROVE` · `REJECT` · `OVERRIDE_OUTPUT` ·
`ESCALATE` · `SUSPEND_SERVICE` · `RETIRE_MODEL` · `OTHER`

## Escalation Channel Values

`HUMAN_REVIEW` · `COMPLIANCE_REVIEW` · `TECHNICAL_REVIEW` · `LEGAL_REVIEW` ·
`MANAGEMENT_APPROVAL` · `OTHER`
