---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Maximum Calibration Error (MCE)
description: Maximum absolute difference between confidence and accuracy across all probability bins. Captures worst-case calibration failure.
tags: [metric, calibration, mce, worst-case, probability, guo-2017]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

MCE complements ECE by capturing worst-case (not average) calibration failure. For high-stakes AI (medical triage, autonomous driving), the worst-case confidence bin matters more than the average. EU AI Act Art. 15 'consistent performance' implies low MCE is required.

**Applies to**: Model | **Sources**: Guo et al. 2017; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-maximum-calibration-error",
  "name": "Maximum Calibration Error (MCE)",
  "description": "Maximum absolute difference between confidence and accuracy across all probabili",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "MCE", "name": "calibration error" },
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

def maximum_calibration_error(y_true, y_prob, n_bins=10):
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    mce = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i+1])
        if mask.sum() == 0:
            continue
        bin_acc  = y_true[mask].mean()
        bin_conf = y_prob[mask].mean()
        mce = max(mce, abs(bin_acc - bin_conf))
    return mce

mce = maximum_calibration_error(y_true, y_prob)
print(f"MCE: {mce:.4f}")
# MCE > 0.15 in any bin is a red flag for AI systems that report confidence scores
```
