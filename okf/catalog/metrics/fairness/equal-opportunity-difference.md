---
type: Metric
title: Equal Opportunity Difference
description: Difference in true positive rates (recall) between the least and most favoured group. Focuses only on correctly identifying positive outcomes.
tags: [metric, fairness, equal-opportunity, tpr-gap, recall-parity, fairlearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Equal opportunity is a relaxed fairness criterion requiring only equal true positive rates, not equal false positive rates. It is appropriate when the harm of missing a positive outcome (false negative) is the primary concern — e.g. benefit eligibility AI, medical diagnosis, creditworthiness.

**Applies to**: Model | **Sources**: Hardt et al. 2016; Fairlearn
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-equal-opportunity-difference",
  "name": "Equal Opportunity Difference",
  "description": "Difference in true positive rates (recall) between the least and most favoured g",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ", "name": "TPR difference" },
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
from fairlearn.metrics import true_positive_rate_difference

eop_diff = true_positive_rate_difference(
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive_features,
)
print(f"Equal Opportunity Difference (TPR gap): {eop_diff:.4f}")
```
