---
type: Metric
title: Distribution Shift — Maximum Mean Discrepancy (MMD)
description: Kernel-based statistical distance between training and deployment feature distributions. Higher MMD means greater distribution shift and higher risk of performance degradation.
tags: [metric, robustness, distribution-shift, mmd, drift, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 9 requires monitoring for 'reasonably foreseeable risks' which include distribution shift. MMD is the standard hypothesis-test-based measure for covariate shift detection. High MMD between training and live data distributions triggers re-validation requirements.

**Applies to**: Dataset, ModelService | **Sources**: Gretton et al. 2012; EU AI Act Art. 9; EU AI Act Art. 12 (logging)
- [EU AI Act Art. 9](../../requirements/eu-ai-act/art9-risk-management.md)
- [Deployment in Unvalidated Context](../../misuse-scenarios/deployment-unvalidated-context.md)

# Instance

```json
{
  "id": "metric-distribution-shift-mmd",
  "name": "Distribution Shift — Maximum Mean Discrepancy (MMD)",
  "description": "Kernel-based statistical distance between training and deployment feature distri",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "MMD²", "name": "squared kernel distance" },
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
import numpy as np
from sklearn.preprocessing import StandardScaler

def mmd_rbf(X: np.ndarray, Y: np.ndarray, gamma: float = 1.0) -> float:
    """Unbiased MMD² estimate with RBF kernel. X: source, Y: target."""    from sklearn.metrics.pairwise import rbf_kernel
    XX = rbf_kernel(X, X, gamma)
    YY = rbf_kernel(Y, Y, gamma)
    XY = rbf_kernel(X, Y, gamma)
    n, m = len(X), len(Y)
    return (XX.sum() - np.trace(XX)) / (n*(n-1))          + (YY.sum() - np.trace(YY)) / (m*(m-1))          - 2 * XY.mean()

scaler = StandardScaler().fit(X_train)
mmd = mmd_rbf(scaler.transform(X_train), scaler.transform(X_live))
print(f"MMD² (train vs live): {mmd:.6f}")
# Use permutation test to determine significance threshold
```
