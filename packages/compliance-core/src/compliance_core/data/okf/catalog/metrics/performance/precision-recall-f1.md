---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Precision, Recall, and F1 Score
description: Composite performance profile: Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = harmonic mean of precision and recall.
tags: [metric, performance, precision, recall, f1, classification, sklearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

F1 is the primary metric for imbalanced classification tasks. EU AI Act Art. 15 mandates appropriate accuracy levels — for medical AI and fraud detection, high recall (minimising false negatives) is typically the compliance requirement. F1 is listed as a standard metric in ISO/IEC 25010:2023 functional correctness criteria.

**Applies to**: Model | **Sources**: sklearn; ISO/IEC 25010:2023; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-precision-recall-f1",
  "name": "Precision, Recall, and F1 Score",
  "description": "Composite performance profile: Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 =",
  "kind": "COMPOSITE",
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
from sklearn.metrics import precision_score, recall_score, f1_score

# For binary classification
precision = precision_score(y_true, y_pred)
recall    = recall_score(y_true, y_pred)
f1        = f1_score(y_true, y_pred)
print(f"Precision: {precision:.4f}  Recall: {recall:.4f}  F1: {f1:.4f}")

# Macro-averaged (equal weight per class — use for multi-class fairness)
f1_macro = f1_score(y_true, y_pred, average="macro")
print(f"Macro F1: {f1_macro:.4f}")

# Per-group F1 (using Fairlearn MetricFrame)
from fairlearn.metrics import MetricFrame
mf = MetricFrame(metrics=f1_score, y_true=y_true, y_pred=y_pred,
                 sensitive_features=sensitive_features)
print(mf.by_group)
print(f"F1 min across groups: {mf.group_min():.4f}")
```
