---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ValueRange
description: Valid value domain for a metric (lower/upper bounds, discreteness, and allowed categories).
tags: [metrics, validation, domain]
schema: ../okb/schemas/ValueRange.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ValueRange` is embedded in [Metric](/metrics/Metric.md) to constrain valid
measurements. For nominal/ordinal metrics, `categories` lists the allowed values.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lower` | number | no | Inclusive lower bound. |
| `upper` | number | no | Inclusive upper bound. |
| `discrete` | boolean | no | Whether values are discrete (integer) rather than continuous. |
| `categories` | list of string | no | Allowed categories for nominal or ordinal scales. |
