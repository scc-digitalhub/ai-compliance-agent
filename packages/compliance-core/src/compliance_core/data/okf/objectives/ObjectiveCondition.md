---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: ObjectiveCondition
description: Condition envelope for a compliance objective — wraps exactly one of threshold, range, categorical, statistical, or composite conditions.
tags: [objective, condition, threshold, range, statistical]
schema: ../okb/schemas/ObjectiveCondition.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ObjectiveCondition` is an envelope that wraps exactly one condition variant. It
is embedded in [ComplianceObjective](/objectives/ComplianceObjective.md) and
referenced as the `expected` snapshot in a `TestResult` inside
[ReportContent](/reports/ReportContent.md).

# Schema

Exactly one of the following fields must be present:

| Field | Type | Description |
|-------|------|-------------|
| `threshold` | ThresholdCondition | Value satisfies `operator(value, threshold)`. |
| `range` | RangeCondition | Value falls within `[lower, upper]`. |
| `categorical` | CategoricalCondition | Value belongs to `allowed` set. |
| `statistical` | StatisticalCondition | Value passes a named statistical hypothesis test. |
| `composite` | CompositeCondition | Logical AND or OR of sub-conditions. |

## ThresholdCondition

| Field | Type | Description |
|-------|------|-------------|
| `operator` | enum | `GEQ` \| `LEQ` \| `GT` \| `LT` \| `EQ` \| `NEQ` |
| `value` | number | Threshold value. |

## RangeCondition

| Field | Type | Description |
|-------|------|-------------|
| `lower` | number | Lower bound. |
| `upper` | number | Upper bound. |
| `inclusive` | boolean | Whether bounds are inclusive. |

## CategoricalCondition

| Field | Type | Description |
|-------|------|-------------|
| `allowed` | set of string | Allowed category values. |

## StatisticalCondition

| Field | Type | Description |
|-------|------|-------------|
| `test` | string | Name of the statistical test (e.g. `chi2`, `ks`). |
| `significance` | number | Significance level (e.g. `0.05`). |
| `hypothesis` | string | Null hypothesis statement. |

## CompositeCondition

| Field | Type | Description |
|-------|------|-------------|
| `operator` | enum | `AND` \| `OR` |
| `conditions` | list of ObjectiveCondition | Sub-conditions (recursive). |
