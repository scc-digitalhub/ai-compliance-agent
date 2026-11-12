---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ConfidenceInterval
description: Statistical confidence interval (lower, upper, confidence level) for a metric result.
tags: [metrics, statistics, uncertainty]
schema: ../okb/schemas/ConfidenceInterval.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ConfidenceInterval` is embedded in [MetricResult](/metrics/MetricResult.md) to
quantify measurement uncertainty.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lower` | number | yes | Inclusive lower bound. |
| `upper` | number | yes | Inclusive upper bound. |
| `level` | number | yes | Confidence level — e.g. `0.95` for 95 %. |
