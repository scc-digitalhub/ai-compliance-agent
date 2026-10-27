---
type: Compliance Model Type
title: MetricComposition
description: Aggregation specification for a composite metric, listing constituent metrics and the combining function.
tags: [metrics, composition, aggregation]
schema: ../okb/schemas/MetricComposition.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`MetricComposition` is embedded in a [Metric](/metrics/Metric.md) with
`kind: COMPOSITE`. It lists the constituent [Metric](/metrics/Metric.md) objects
and the aggregation function that combines them.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `components` | list of [Metric](/metrics/Metric.md) | yes | Constituent metrics (embedded). |
| `aggregation` | enum | yes | `MEAN` \| `MIN` \| `MAX` \| `SUM` \| `PRODUCT` \| `OTHER` |
| `custom_fn` | string | no | Description of the aggregation when `aggregation` is `OTHER`. |
