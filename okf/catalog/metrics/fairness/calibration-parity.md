---
type: Metric
title: Calibration Parity (Group Calibration Gap)
description: Maximum difference in Expected Calibration Error (ECE) across demographic groups. Zero means the model is equally calibrated for all groups.
tags: [metric, fairness, calibration-parity, ece, group-calibration, fairness]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

A model that is well-calibrated overall may be miscalibrated for minority groups, causing systematic over- or under-confidence in predictions for those groups. Calibration parity detects this by computing ECE per group and reporting the maximum gap.

**Applies to**: Model | **Sources**: Chouldechova 2017; Pleiss et al. 2017; Fairlearn
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-calibration-parity",
  "name": "Calibration Parity (Group Calibration Gap)",
  "description": "Maximum difference in Expected Calibration Error (ECE) across demographic groups",
  "kind": "COMPOSITE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ ECE", "name": "calibration gap" },
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
import numpy as np
from sklearn.calibration import calibration_curve

def expected_calibration_error(y_true, y_prob, n_bins=10):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    bin_sizes = np.histogram(y_prob, bins=n_bins)[0]
    weights = bin_sizes / len(y_prob)
    return float(np.sum(weights[:len(prob_true)] * np.abs(prob_true - prob_pred)))

groups = np.unique(sensitive_features)
ece_per_group = {
    g: expected_calibration_error(
        y_true[sensitive_features == g],
        y_prob[sensitive_features == g],
    )
    for g in groups
}
calibration_gap = max(ece_per_group.values()) - min(ece_per_group.values())
print(f"ECE per group: {ece_per_group}")
print(f"Calibration Parity Gap: {calibration_gap:.4f}")
```
