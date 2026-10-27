---
type: Metric
title: Demographic Representativeness Gap
description: Maximum absolute difference between the proportion of a demographic group in the dataset and its proportion in the target deployment population.
tags: [metric, data-quality, representativeness, demographic-gap, eu-ai-act, bias]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 10 requires datasets to have 'appropriate statistical properties including as regards persons or groups on which the AI system is intended to be used'. A large representativeness gap indicates the training distribution does not reflect the deployment population, introducing demographic bias.

**Applies to**: Dataset | **Sources**: EU AI Act Art. 10; ISO/IEC TR 24027; Fairlearn
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)
- [GDPR Art. 35](../../requirements/gdpr/art35-dpia.md)

# Instance

```json
{
  "id": "metric-representativeness-gap",
  "name": "Demographic Representativeness Gap",
  "description": "Maximum absolute difference between the proportion of a demographic group in the",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ%", "name": "proportion difference" },
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
import pandas as pd

def representativeness_gap(
    df: pd.DataFrame,
    protected_col: str,
    reference_distribution: dict,
) -> float:
    """Max absolute diff between dataset and reference population proportions."""
    dataset_dist = df[protected_col].value_counts(normalize=True)
    gaps = []
    for group, ref_prop in reference_distribution.items():
        dataset_prop = dataset_dist.get(group, 0.0)
        gaps.append(abs(dataset_prop - ref_prop))
    return max(gaps)

# Reference: expected proportions in deployment population (e.g. from census)
reference = {"M": 0.49, "F": 0.49, "NB": 0.02}
gap = representativeness_gap(df_train, "gender", reference)
print(f"Max representativeness gap: {gap:.4f}")
# Gap > 0.05 warrants investigation and possible resampling
```
