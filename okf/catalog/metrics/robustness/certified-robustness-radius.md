---
type: Metric
title: Certified Robustness Radius
description: Minimum L2-norm perturbation radius within which the model is guaranteed (with high probability) to return the same prediction. Higher radius means stronger certified robustness.
tags: [metric, robustness, certified, randomized-smoothing, nist-ai-100-2]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Certified robustness provides provable, not just empirical, guarantees. Randomised smoothing (Cohen et al. 2019) enables efficient certification for any classifier. NIST AI 100-2 identifies certification as a key mitigation for evasion attacks. Particularly relevant for safety-critical EU AI Act Annex I systems.

**Applies to**: Model | **Sources**: Cohen et al. 2019; NIST AI 100-2; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-certified-robustness-radius",
  "name": "Certified Robustness Radius",
  "description": "Minimum L2-norm perturbation radius within which the model is guaranteed (with h",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "r", "name": "L2 radius" },
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
# Using the 'smoothed_classifier' approach (Cohen et al. 2019)
import numpy as np
from scipy.stats import norm

def certified_radius(p_A: float, sigma: float) -> float:
    """
    p_A: smoothed classifier's probability for the top class (estimated by Monte Carlo)
    sigma: Gaussian noise std used for smoothing
    Returns certified radius (L2) or -1 if certification fails (p_A < 0.5).
    """
    if p_A < 0.5:
        return -1.0
    return sigma * norm.ppf(p_A)

# Example: estimate p_A by sampling
n_samples = 1000
sigma = 0.25
noise = np.random.randn(n_samples, *x.shape) * sigma
smoothed_preds = np.argmax(model.predict(x + noise), axis=-1)
p_A_hat = np.mean(smoothed_preds == top_class)

radius = certified_radius(p_A_hat, sigma)
print(f"Estimated p_A: {p_A_hat:.4f}")
print(f"Certified radius: {radius:.4f}")
```
