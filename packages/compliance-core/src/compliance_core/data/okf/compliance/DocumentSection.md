---
type: Compliance Model Type
title: DocumentSection
description: A titled, structured section within a ComplianceDocumentation artifact, supporting Markdown content, nested subsections, a machine-readable specification, and report references.
tags: [compliance, documentation, section, model-card, data-card]
schema: ../okb/schemas/DocumentSection.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`DocumentSection` is the building block of
[ComplianceDocumentation](/compliance/ComplianceDocumentation.md). Sections can
nest via `subsections`. The `format` field aligns each section to a specific card
standard. Reports backing the section's claims are referenced via
[EntityRef](/foundations/EntityRef.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Section heading. |
| `content` | string | no | Markdown body of the section. |
| `format` | enum | no | `MODELCARD` \| `DATACARD` \| `SYSTEMCARD` \| `OTHER` |
| `format_value` | string | no | Free text when `format` is `OTHER`. |
| `subsections` | list of DocumentSection | no | Nested child sections (recursive). |
| `specification` | map (string → any) | no | Machine-readable structured representation. |
| `reports` | list of [EntityRef](/foundations/EntityRef.md) | no | References to supporting report entities. |
