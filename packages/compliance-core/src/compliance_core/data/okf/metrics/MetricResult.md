---
type: Compliance Model Type
title: MetricResult
description: Observed value of a single metric within an evaluation report, with optional confidence interval.
tags: [metrics, measurement, result, evaluation]
schema: ../okb/schemas/MetricResult.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`MetricResult` records a single observed measurement inside an
`EvaluationContent` (see [ReportContent](/reports/ReportContent.md)). The `value`
field is polymorphic (number, string, boolean, or map). Statistical uncertainty
is captured in the optional [ConfidenceInterval](/metrics/ConfidenceInterval.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metric` | [Metric](/metrics/Metric.md) | yes | The metric that was measured (embedded). |
| `value` | any | yes | Observed value — number, string, boolean, or key-value map. |
| `confidence` | [ConfidenceInterval](/metrics/ConfidenceInterval.md) | no | Statistical confidence interval. |
| `computed_at` | datetime | yes | When the value was computed. |
