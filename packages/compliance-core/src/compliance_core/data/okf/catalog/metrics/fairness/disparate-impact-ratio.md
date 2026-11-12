---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Disparate Impact Ratio
description: Ratio of positive prediction rates between the least and most favoured group. US EEOC 80% rule: ratio < 0.8 signals adverse impact.
tags: [metric, fairness, disparate-impact, group-fairness, eeoc-80-rule, aif360]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The 80% rule (EEOC four-fifths rule) treats a disparate impact ratio below 0.8 as prima facie evidence of adverse impact. EU AI Act Art. 10 bias examination implicitly targets this metric for high-risk AI.

**Applies to**: Model, ModelService | **Sources**: AI Fairness 360; EEOC Uniform Guidelines; EU AI Act Art. 10
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-disparate-impact-ratio",
  "name": "Disparate Impact Ratio",
  "description": "Ratio of positive prediction rates between the least and most favoured group. US",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "ratio", "name": "rate ratio" },
  "range": {
    "lower": 0.0,
    "upper": null,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
from aif360.metrics import BinaryLabelDatasetMetric

# Wrap predictions in an AIF360 dataset
from aif360.datasets import BinaryLabelDataset
import pandas as pd

df_pred = pd.DataFrame({
    "outcome": y_pred,
    "protected_attr": sensitive_features,
})
dataset = BinaryLabelDataset(
    df=df_pred,
    label_names=["outcome"],
    protected_attribute_names=["protected_attr"],
)
metric = BinaryLabelDatasetMetric(
    dataset,
    unprivileged_groups=[{"protected_attr": 0}],
    privileged_groups=[{"protected_attr": 1}],
)
dir_score = metric.disparate_impact()
print(f"Disparate Impact Ratio: {dir_score:.4f}")
# Threshold: >= 0.8 (EEOC rule), >= 0.9 (stricter)
```
