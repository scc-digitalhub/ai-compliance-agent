---
type: Compliance Model Type
title: ComplianceStatus
description: Assessed compliance status of a project or entity at a point in time, including findings and mitigation actions.
tags: [compliance, status, finding, mitigation, assessment]
schema: ../okb/schemas/ComplianceStatus.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceStatus` captures the compliance verdict for an entity at a specific
point in time. It is embedded in [ComplianceSpec](/specs/ComplianceSpec.md).
Non-conformances are listed as [ComplianceFinding](/compliance/ComplianceFinding.md)
objects, and active remediation efforts appear as
[MitigationAction](/compliance/MitigationAction.md) objects.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | `COMPLIANT` \| `NON_COMPLIANT` \| `PARTIALLY_COMPLIANT` \| `PENDING_REVIEW` |
| `assessed_at` | datetime | yes | When the assessment was performed. |
| `assessor` | [ActorRef](/foundations/ActorRef.md) | yes | Who performed the assessment. |
| `findings` | set of [ComplianceFinding](/compliance/ComplianceFinding.md) | no | Non-conformances detected. |
| `mitigations` | set of [MitigationAction](/compliance/MitigationAction.md) | no | Active or completed remediation actions. |
