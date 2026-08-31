---
type: Compliance Documentation
title: ComplianceDocumentation
description: Lightweight structured documentation artifact scoped to the compliance dimension of an entity, composed of titled sections.
tags: [compliance, documentation, model-card, data-card, system-card]
schema: ../okb/schemas/ComplianceDocumentation.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceDocumentation` is a lightweight, embedded documentation artefact — not
a standalone entity. It is always nested inside [ComplianceSpec](/specs/ComplianceSpec.md)
and conforms to the Model Card, Data Card, and System Card standards through the
`format` field of its [DocumentSection](/compliance/DocumentSection.md) entries.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sections` | list of [DocumentSection](/compliance/DocumentSection.md) | no | Ordered list of documentation sections. |
