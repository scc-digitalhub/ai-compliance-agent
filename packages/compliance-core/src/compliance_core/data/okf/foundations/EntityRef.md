---
type: Compliance Model Type
title: EntityRef
description: Opaque cross-entity reference key used to link compliance objects without embedding full graphs.
tags: [foundation, reference, link]
schema: ../okb/schemas/EntityRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`EntityRef` is a single-field wrapper holding an opaque `key` that uniquely
addresses any first-class entity in the platform. It is used wherever a compliance
object must point at a report, finding, or evidence artifact without embedding the
full object.

Used by: [ComplianceFinding](/compliance/ComplianceFinding.md) (report),
[MitigationAction](/compliance/MitigationAction.md) (evidence, verification_report),
[DocumentSection](/compliance/DocumentSection.md) (reports).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | string | yes | Opaque reference key (typically a composite `id::kind` string). |

# Examples

```json
{ "key": "report::12a4f8b2-eval" }
```
