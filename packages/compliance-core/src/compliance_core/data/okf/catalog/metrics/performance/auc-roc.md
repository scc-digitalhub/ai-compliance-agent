---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: AUC-ROC (Area Under ROC Curve)
description: Area under the Receiver Operating Characteristic curve. Measures the model's ability to discriminate between classes across all decision thresholds.
tags: [metric, performance, auc-roc, discrimination, ranking, sklearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

AUC-ROC is threshold-independent and provides a holistic view of model discriminative ability. It is widely used as an accuracy metric in EU AI Act Art. 15 compliance thresholds for medical device AI, credit scoring, and fraud detection (EU AI Act Annex III). AUC ≥ 0.85 is a common minimum threshold for high-risk AI.

**Applies to**: Model | **Sources**: sklearn; ISO/IEC 25010:2023; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-auc-roc",
  "name": "AUC-ROC (Area Under ROC Curve)",
  "description": "Area under the Receiver Operating Characteristic curve. Measures the model's abi",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "AUC", "name": "area" },
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
from sklearn.metrics import roc_auc_score, RocCurveDisplay
import matplotlib.pyplot as plt

# For binary probabilistic classifier
auc = roc_auc_score(y_true, y_prob)
print(f"AUC-ROC: {auc:.4f}")

# Multi-class (one-vs-rest)
auc_ovr = roc_auc_score(y_true_mc, y_prob_mc, multi_class="ovr", average="macro")
print(f"Macro AUC (OvR): {auc_ovr:.4f}")

# Plot ROC curve
fig, ax = plt.subplots()
RocCurveDisplay.from_predictions(y_true, y_prob, ax=ax)
plt.savefig("roc_curve.png")
```
