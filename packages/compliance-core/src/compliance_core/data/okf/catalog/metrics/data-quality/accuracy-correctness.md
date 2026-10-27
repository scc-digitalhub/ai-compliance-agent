---
type: Metric
title: Data Accuracy / Correctness Rate
description: Fraction of data values that correctly represent the real-world entity they describe, measured against a reference or through validation rules.
tags: [metric, data-quality, accuracy, correctness, iso-8000, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

ISO 8000 accuracy is the degree to which data correctly describes the real-world object. EU AI Act Art. 10 requires training data to be 'free of errors to the best extent possible'. Measured as fraction passing validation rules or matching a gold-standard reference.

**Applies to**: Dataset | **Sources**: ISO 8000; EU AI Act Art. 10; DAMA DMBOK
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-data-accuracy",
  "name": "Data Accuracy / Correctness Rate",
  "description": "Fraction of data values that correctly represent the real-world entity they desc",
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
from typing import Callable, Dict

def accuracy_rate(
    df: pd.DataFrame,
    rules: Dict[str, Callable],
) -> float:
    """Fraction of rows passing all validation rules."""
    mask = pd.Series(True, index=df.index)
    for col, rule in rules.items():
        mask &= df[col].apply(rule)
    return mask.mean()

# Example: age must be 0-120, income must be non-negative
rules = {
    "age": lambda v: 0 <= v <= 120,
    "income": lambda v: v >= 0,
}
rate = accuracy_rate(df, rules)
print(f"Data accuracy rate: {rate:.4f}")
```
