---
type: Metric
title: Label Balance Ratio
description: Ratio of the minority class count to the majority class count in a classification dataset. A value of 1.0 is perfectly balanced.
tags: [metric, data-quality, class-imbalance, label-balance, training-data]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Class imbalance causes models to be biased towards the majority class, resulting in high false negative rates for minority classes. This is especially harmful in high-stakes AI (medical diagnosis, fraud detection) where the minority class is typically the most important. EU AI Act Art. 10 requires datasets to have appropriate statistical properties.

**Applies to**: Dataset | **Sources**: EU AI Act Art. 10; ISO/IEC TR 24027; Fairlearn
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-label-balance-ratio",
  "name": "Label Balance Ratio",
  "description": "Ratio of the minority class count to the majority class count in a classificatio",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "ratio", "name": "minority/majority ratio" },
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

def label_balance_ratio(y: pd.Series) -> float:
    counts = y.value_counts()
    return counts.min() / counts.max()

ratio = label_balance_ratio(df["label"])
print(f"Label balance ratio: {ratio:.4f}")
# < 0.1 : severe imbalance → consider oversampling or class weighting
# < 0.5 : moderate imbalance → monitor per-class metrics
print(df["label"].value_counts(normalize=True))
```
