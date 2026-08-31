---
type: Compliance Model Type
title: FieldSpec
description: Schema field descriptor used in tabular dataset schemas and as model input/output specifications.
tags: [data, schema, model, field, sensitivity]
schema: ../okb/schemas/FieldSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`FieldSpec` describes a single column or feature, carrying data type, nullability,
and a [sensitivity classification](/data/DataGovernance.md). It is used in tabular
`SchemaSpec` and in the inputs/outputs of [InferenceSignature](/model/InferenceSignature.md)
(as a flat-feature alternative to `TensorSpec`).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Field name. |
| `dtype` | enum | yes | Data type — `INT` · `FLOAT` · `STRING` · `BOOL` · `STRUCT` · `ARRAY` · `MAP` · `BYTES` · `DATE` · `DATETIME` · `CUSTOM` |
| `nullable` | boolean | yes | Whether the field accepts null values. |
| `description` | string | no | Human-readable description. |
| `sensitivity` | enum | no | `NONE` \| `PII` \| `SENSITIVE` \| `RESTRICTED` \| `PROHIBITED` |
| `tags` | set of string | no | Free-form classification tags. |
