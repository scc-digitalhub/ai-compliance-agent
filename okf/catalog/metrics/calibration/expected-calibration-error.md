---
type: Metric
title: Expected Calibration Error (ECE)
description: Weighted average absolute difference between predicted confidence and empirical accuracy across probability bins. Perfect calibration = 0.
tags: [metric, calibration, ece, probability, confidence, guo-2017, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

A well-calibrated model produces confidence scores that match actual correctness rates. EU AI Act Art. 15 requires consistent performance throughout the lifecycle; miscalibration causes systematic over- or under-confidence in AI-assisted decisions. ECE is the primary calibration metric for high-risk AI (medical, credit, legal).

**Applies to**: Model | **Sources**: Guo et al. 2017; EU AI Act Art. 15; sklearn
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-expected-calibration-error",
  "name": "Expected Calibration Error (ECE)",
  "description": "Weighted average absolute difference between predicted confidence and empirical ",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "ECE", "name": "calibration error" },
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
    """ECE: weighted mean |accuracy - confidence| across bins."""    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i+1])
        if mask.sum() == 0:
            continue
        bin_acc  = y_true[mask].mean()
        bin_conf = y_prob[mask].mean()
        ece += mask.mean() * abs(bin_acc - bin_conf)
    return ece

ece = expected_calibration_error(y_true, y_prob)
print(f"ECE: {ece:.4f}")
# ECE < 0.05 is generally acceptable; < 0.02 for high-stakes AI

# sklearn alternative (requires calibration_curve)
from sklearn.calibration import CalibrationDisplay
CalibrationDisplay.from_predictions(y_true, y_prob, n_bins=10)
```
