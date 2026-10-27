---
type: Metric
title: Average Odds Difference
description: Average of the absolute differences in TPR and FPR between unprivileged and privileged group. Zero indicates equal error rates.
tags: [metric, fairness, average-odds, tpr, fpr, aif360]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Average odds difference balances TPR and FPR parity, making it useful when both false negatives and false positives have significant costs. Used in AI Fairness 360 as a primary classification fairness metric.

**Applies to**: Model | **Sources**: AI Fairness 360; Hardt et al. 2016
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-average-odds-difference",
  "name": "Average Odds Difference",
  "description": "Average of the absolute differences in TPR and FPR between unprivileged and priv",
  "kind": "COMPOSITE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ", "name": "average rate difference" },
  "range": {
    "lower": -1.0,
    "upper": 1.0,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
from aif360.metrics import ClassificationMetric
from aif360.datasets import BinaryLabelDataset
import pandas as pd

def make_aif360_dataset(y, sens):
    df = pd.DataFrame({"label": y, "protected": sens})
    return BinaryLabelDataset(df=df, label_names=["label"],
                               protected_attribute_names=["protected"])

ds_true = make_aif360_dataset(y_true, sensitive_features)
ds_pred = make_aif360_dataset(y_pred, sensitive_features)

metric = ClassificationMetric(
    ds_true, ds_pred,
    unprivileged_groups=[{"protected": 0}],
    privileged_groups=[{"protected": 1}],
)
aod = metric.average_odds_difference()
print(f"Average Odds Difference: {aod:.4f}")
```
