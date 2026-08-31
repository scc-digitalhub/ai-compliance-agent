---
type: Compliance Model Type
title: UnitOfMeasure
description: Physical or logical unit of measurement for a metric value (symbol and display name).
tags: [metrics, unit, measurement]
schema: ../okb/schemas/UnitOfMeasure.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`UnitOfMeasure` is embedded in [Metric](/metrics/Metric.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | yes | Short symbol — e.g. `%`, `ms`, `tokens/s`. |
| `name` | string | yes | Full name — e.g. `percent`, `milliseconds`. |
