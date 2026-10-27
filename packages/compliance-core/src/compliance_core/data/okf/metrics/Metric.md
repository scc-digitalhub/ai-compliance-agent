---
type: Compliance Metric
title: Metric
description: Quantitative or qualitative measure of a defined notion; primitive metrics compose into composite metrics via MetricComposition.
tags: [metrics, measurement, fairness, performance, quality]
schema: ../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`Metric` is the measurement atom of the framework. A `PRIMITIVE` metric has no
`composition`; a `COMPOSITE` metric carries a [MetricComposition](/metrics/MetricComposition.md)
that references its constituent metrics.

Metrics are bound to [ComplianceObjective](/objectives/ComplianceObjective.md)s
and their values are recorded as [MetricResult](/metrics/MetricResult.md)s inside
[ReportContent](/reports/ReportContent.md).

Extends [BaseComplianceObject](/foundations/BaseComplianceObject.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | *(from BaseComplianceObject)* |
| `namespace` | string | no | *(from BaseComplianceObject)* |
| `name` | string | yes | *(from BaseComplianceObject)* — e.g. `equalized_odds_difference`. |
| `description` | string | no | *(from BaseComplianceObject)* |
| `kind` | enum | yes | `PRIMITIVE` \| `COMPOSITE` |
| `scale` | enum | yes | `NOMINAL` \| `ORDINAL` \| `INTERVAL` \| `RATIO` \| `BOOLEAN` |
| `unit` | [UnitOfMeasure](/metrics/UnitOfMeasure.md) | no | Physical unit (e.g. `%`, `ms`). |
| `range` | [ValueRange](/metrics/ValueRange.md) | no | Valid value domain. |
| `composition` | [MetricComposition](/metrics/MetricComposition.md) | no | Required when `kind` is `COMPOSITE`. |

# Examples

```json
{
  "id": "eod-001",
  "name": "Equalized Odds Difference",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "", "name": "dimensionless" },
  "range": { "lower": 0.0, "upper": 1.0, "discrete": false }
}
```
