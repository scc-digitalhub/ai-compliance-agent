---
type: Metric
title: Feature Importance Stability (Rank Correlation)
description: Spearman rank correlation of feature importance scores between two inference runs on slightly perturbed identical inputs. High stability means explanations are consistent and reliable.
tags: [metric, explainability, stability, consistency, shap, rank-correlation]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Unstable explanations — where small input perturbations change feature importance rankings significantly — erode trust and may indicate explanation method fragility. EU HLEG ALTAI requires explanations to be 'consistent and replicable'. Spearman ρ > 0.9 is a reasonable stability threshold.

**Applies to**: Model | **Sources**: Alvarez-Melis & Jaakkola 2018; EU HLEG ALTAI 2020
- [EU AI Act Art. 13](../../requirements/eu-ai-act/art13-transparency.md)

# Instance

```json
{
  "id": "metric-feature-importance-stability",
  "name": "Feature Importance Stability (Rank Correlation)",
  "description": "Spearman rank correlation of feature importance scores between two inference run",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "ρ", "name": "Spearman rho" },
  "range": {
    "lower": -1.0,
    "upper": 1.0,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
import numpy as np
import shap
from scipy.stats import spearmanr

explainer = shap.TreeExplainer(model)

def get_importance(x):
    sv = explainer.shap_values(x[np.newaxis, :])
    return np.abs(sv[0] if isinstance(sv, list) else sv[0])

rhos = []
for i in range(min(50, len(X_test))):
    x = X_test[i]
    noise = np.random.randn(*x.shape) * 0.01  # tiny perturbation
    imp1 = get_importance(x)
    imp2 = get_importance(x + noise)
    rho, _ = spearmanr(imp1, imp2)
    rhos.append(rho)

print(f"Mean feature importance stability (Spearman ρ): {np.mean(rhos):.4f}")
# ρ < 0.9 indicates instability; investigate explanation method
```
