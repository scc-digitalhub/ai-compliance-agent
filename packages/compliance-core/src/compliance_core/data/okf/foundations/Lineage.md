---
type: Compliance Model Type
title: Lineage
description: DAG of derivation relationships tracking how an artifact was produced.
tags: [foundation, provenance, lineage, traceability]
schema: ../okb/schemas/Lineage.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`Lineage` carries the provenance chain for any artifact: which upstream artifacts
were consumed and which operation run produced it. It is embedded in Data, Model,
and [ReportContent](/reports/ReportContent.md) objects.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sources` | list of string | no | Identifiers of upstream artifacts consumed. |
| `operation` | string | no | Identifier of the operation run that produced this artifact. |

# Examples

```json
{
  "sources": ["dataitem::training-v3", "dataitem::validation-v2"],
  "operation": "run::train-001"
}
```
