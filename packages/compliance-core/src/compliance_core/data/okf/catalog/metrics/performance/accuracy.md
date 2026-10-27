---
type: Metric
title: Classification Accuracy
description: Fraction of predictions that match the true label. Equivalent to (TP + TN) / total.
tags: [metric, performance, accuracy, classification, sklearn, iso-25010]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 requires high-risk AI to 'achieve appropriate levels of accuracy'. Accuracy is the primary performance metric for compliance thresholds but should be supplemented by per-class and per-group metrics when class imbalance or protected groups are present.

**Applies to**: Model, ModelService | **Sources**: sklearn; ISO/IEC 25010:2023; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-accuracy",
  "name": "Classification Accuracy",
  "description": "Fraction of predictions that match the true label. Equivalent to (TP + TN) / tot",
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
from sklearn.metrics import accuracy_score, balanced_accuracy_score

acc = accuracy_score(y_true, y_pred)
bal_acc = balanced_accuracy_score(y_true, y_pred)  # recommended for imbalanced data
print(f"Accuracy: {acc:.4f}")
print(f"Balanced Accuracy: {bal_acc:.4f}")

# Per-class accuracy
from sklearn.metrics import classification_report
print(classification_report(y_true, y_pred))
```
