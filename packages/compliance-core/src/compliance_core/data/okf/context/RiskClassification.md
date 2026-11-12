---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: RiskClassification
description: Risk classification of an AI system within a compliance context, including level, status, and review schedule.
tags: [context, risk, classification, eu-ai-act]
schema: ../okb/schemas/RiskClassification.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`RiskClassification` captures the EU AI Act (or equivalent) risk tier assigned to
an AI system and the governance evidence around that assignment (assessor, approver,
validity period, review cadence). It is embedded in
[ComplianceContext](/context/ComplianceContext.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `risk_level` | enum | yes | `PROHIBITED` \| `HIGH` \| `LIMITED` \| `MINIMAL` \| `UNKNOWN` \| `OTHER` |
| `risk_level_value` | string | no | Free text when `risk_level` is `OTHER`. |
| `classification_status` | enum | yes | `PRELIMINARY` \| `ASSESSED` \| `APPROVED` \| `NEEDS_REVIEW` \| `SUPERSEDED` |
| `rationale` | string | no | Reasoning for the assigned risk level. |
| `assessor` | [ActorRef](/foundations/ActorRef.md) | no | Who performed the assessment. |
| `approver` | [ActorRef](/foundations/ActorRef.md) | no | Who approved the classification. |
| `assessed_at` | datetime | no | When the assessment was made. |
| `valid_until` | datetime | no | Expiry of this classification. |
| `review_cadence` | duration | no | ISO-8601 duration between mandated reviews (e.g. `P1Y`). |
