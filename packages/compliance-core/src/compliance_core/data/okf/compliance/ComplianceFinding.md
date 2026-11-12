---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ComplianceFinding
description: A non-conformance finding produced during a compliance assessment, linking to the violated objective and the evidence report.
tags: [compliance, finding, non-conformance, evidence]
schema: ../okb/schemas/ComplianceFinding.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceFinding` records a single non-conformance within
[ComplianceStatus](/compliance/ComplianceStatus.md). It links the finding to the
violated [ComplianceObjective](/objectives/ComplianceObjective.md) (by `id` string)
and to the Report that produced the evidence (via [EntityRef](/foundations/EntityRef.md)).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Human-readable description of the non-conformance. |
| `objective` | string | yes | Identifier of the violated [ComplianceObjective](/objectives/ComplianceObjective.md). |
| `report` | [EntityRef](/foundations/EntityRef.md) | yes | Reference to the report that recorded the violation. |
