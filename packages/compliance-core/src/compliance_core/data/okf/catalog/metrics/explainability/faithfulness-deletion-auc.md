---
type: Metric
title: Explanation Faithfulness — Deletion AUC
description: Area under the prediction-vs-feature-deletion curve. Features are removed in order of importance; fast prediction drop indicates faithful explanations.
tags: [metric, explainability, faithfulness, deletion, feature-attribution]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Faithfulness measures whether attribution scores correctly reflect the model's actual reliance on features. The deletion metric (Samek et al. 2017) removes features in importance order and measures prediction degradation — high degradation = faithful attribution. EU AI Act Art. 13 requires explanations that are not misleading.

**Applies to**: Model | **Sources**: Samek et al. 2017; Hooker et al. 2019; EU AI Act Art. 13
- [EU AI Act Art. 13](../../requirements/eu-ai-act/art13-transparency.md)

# Instance

```json
{
  "id": "metric-faithfulness-deletion-auc",
  "name": "Explanation Faithfulness — Deletion AUC",
  "description": "Area under the prediction-vs-feature-deletion curve. Features are removed in ord",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "AUC", "name": "area" },
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

def deletion_auc(model_predict, X, feature_importance_order, baseline=0.0):
    """
    Sequentially mask features (replace with baseline) in importance order.
    Returns AUC of the prediction score vs. fraction of features deleted.
    A lower AUC means faster performance drop = more faithful explanation.
    """
    n_features = X.shape[1]
    scores = []
    X_masked = X.copy()
    for i, feat_idx in enumerate(feature_importance_order):
        X_masked[:, feat_idx] = baseline
        preds = model_predict(X_masked)
        scores.append(np.mean(preds))  # mean predicted probability of positive
    return np.trapz(scores, dx=1.0 / n_features)

# Get feature importance order from SHAP
importance_order = mean_shap.argsort()[::-1].values  # descending

del_auc = deletion_auc(model.predict_proba_pos, X_test, importance_order)
print(f"Deletion AUC: {del_auc:.4f}")
# Lower AUC = more faithful (explanation matches model reasoning)
```
