---
type: Metric
title: Log-Loss (Cross-Entropy Loss)
description: Negative log-likelihood of predicted probabilities given true labels. Lower is better; 0 is perfect. Measures both discrimination and calibration jointly.
tags: [metric, performance, log-loss, cross-entropy, probabilistic, sklearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Log-loss rewards confident and correct predictions while heavily penalising confident and wrong predictions. It is the primary training loss for probabilistic classifiers and a key metric for models whose output is a probability (risk scores, confidence scores used in high-risk AI decisions).

**Applies to**: Model | **Sources**: sklearn; ISO/IEC 25010:2023
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-log-loss",
  "name": "Log-Loss (Cross-Entropy Loss)",
  "description": "Negative log-likelihood of predicted probabilities given true labels. Lower is b",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "nats", "name": "nats" },
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
from sklearn.metrics import log_loss

ll = log_loss(y_true, y_prob)
print(f"Log-Loss: {ll:.4f}")
# Random classifier (binary) baseline: ln(2) ≈ 0.693

# Per-group log-loss (detect differential confidence quality)
import numpy as np
groups = np.unique(sensitive_features)
for g in groups:
    mask = sensitive_features == g
    g_ll = log_loss(y_true[mask], y_prob[mask])
    print(f"  Group {g} Log-Loss: {g_ll:.4f}")
```
