---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Data Consistency Rate
description: Fraction of records that satisfy all defined cross-field and referential integrity constraints. Inconsistent records violate logical rules within the dataset.
tags: [metric, data-quality, consistency, integrity, iso-8000]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

ISO 8000 consistency measures whether data values do not contradict each other. Inconsistent training data (e.g. contradictory labels for identical feature vectors) degrades model quality and may introduce bias.

**Applies to**: Dataset | **Sources**: ISO 8000; DAMA DMBOK
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-data-consistency",
  "name": "Data Consistency Rate",
  "description": "Fraction of records that satisfy all defined cross-field and referential integri",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "%", "name": "percent" },
  "range": {
    "lower": 0.0,
    "upper": 1.0,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
import pandas as pd

def consistency_rate(df: pd.DataFrame, constraints: list) -> float:
    """Fraction of rows satisfying all cross-field constraints.
    constraints: list of boolean Series (one per constraint).
    """
    mask = pd.Series(True, index=df.index)
    for c in constraints:
        mask &= c
    return mask.mean()

# Example: start_date must be before end_date; if employed then employment_status != 'UNEMPLOYED'
constraints = [
    df["start_date"] <= df["end_date"],
    ~((df["hours_worked"] > 0) & (df["employment_status"] == "UNEMPLOYED")),
]
rate = consistency_rate(df, constraints)
print(f"Consistency rate: {rate:.4f}")
```
