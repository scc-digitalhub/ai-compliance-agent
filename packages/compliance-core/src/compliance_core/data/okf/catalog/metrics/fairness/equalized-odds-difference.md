---
type: Metric
title: Equalized Odds Difference
description: Maximum absolute difference in true positive rate and false positive rate across groups. Zero means equal TPR and FPR for all groups.
tags: [metric, fairness, equalized-odds, tpr, fpr, group-fairness, fairlearn, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Equalized odds requires a model to have equal true positive rate and false positive rate across demographic groups. This is the most demanding standard fairness criterion and is directly implied by EU AI Act Art. 10 and GDPR Art. 22 non-discrimination obligations.

**Applies to**: Model | **Sources**: Hardt et al. 2016; Fairlearn; EU AI Act Art. 10
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)
- [EU Charter Art. 21](../../requirements/eu-charter/art21-non-discrimination.md)

# Instance

```json
{
  "id": "metric-equalized-odds-difference",
  "name": "Equalized Odds Difference",
  "description": "Maximum absolute difference in true positive rate and false positive rate across",
  "kind": "COMPOSITE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ", "name": "rate difference" },
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
from fairlearn.metrics import equalized_odds_difference

eod = equalized_odds_difference(
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive_features,
)
print(f"Equalized Odds Difference: {eod:.4f}")
# Decompose into TPR and FPR gaps:
from fairlearn.metrics import MetricFrame
from sklearn.metrics import true_positive_rate, false_positive_rate
mf = MetricFrame(
    metrics={"tpr": true_positive_rate, "fpr": false_positive_rate},
    y_true=y_true, y_pred=y_pred,
    sensitive_features=sensitive_features,
)
print(mf.by_group)
```
