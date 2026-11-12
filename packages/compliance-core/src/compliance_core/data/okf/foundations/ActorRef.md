---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ActorRef
description: Reference to a human user, service account, or automated agent that performed an action.
tags: [foundation, identity, actor, audit]
schema: ../okb/schemas/ActorRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ActorRef` identifies *who* performed a compliance-relevant action. It appears in
[RiskClassification](/context/RiskClassification.md) (assessor, approver),
[RetentionPolicy](/data/RetentionPolicy.md) (owner, approver),
[ComplianceStatus](/compliance/ComplianceStatus.md) (assessor),
and [MitigationAction](/compliance/MitigationAction.md) (owner).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | enum | yes | `HUMAN` \| `SERVICE` \| `AGENT` |
| `id` | string | yes | Identity string — e.g. OIDC subject, service principal name. |

# Examples

```json
{ "kind": "HUMAN",   "id": "alice@example.com" }
{ "kind": "SERVICE", "id": "compliance-pipeline/v2" }
{ "kind": "AGENT",   "id": "validation-agent/gemini-2.5-pro" }
```
