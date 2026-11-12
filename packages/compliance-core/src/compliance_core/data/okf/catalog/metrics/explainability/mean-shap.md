---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Mean |SHAP| Feature Importance
description: Mean absolute SHAP value per feature across the test set, ranking features by their average contribution to model output. Higher value = higher importance.
tags: [metric, explainability, shap, feature-importance, transparency, eu-hleg-altai]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

SHAP (SHapley Additive exPlanations) provides theoretically grounded, model-agnostic feature attributions. EU HLEG ALTAI requires explainability appropriate to the context. Mean |SHAP| is the primary global importance metric for compliance documentation (EU AI Act Art. 13 instructions for use).

**Applies to**: Model | **Sources**: Lundberg & Lee 2017; EU HLEG ALTAI 2020; EU AI Act Art. 13
- [EU AI Act Art. 13](../../requirements/eu-ai-act/art13-transparency.md)
- [UNESCO Transparency](../../requirements/unesco/transparency.md)

# Instance

```json
{
  "id": "metric-mean-shap-importance",
  "name": "Mean |SHAP| Feature Importance",
  "description": "Mean absolute SHAP value per feature across the test set, ranking features by th",
  "kind": "COMPOSITE",
  "scale": "RATIO",
  "unit": { "symbol": "|Δŷ|", "name": "mean absolute output impact" },
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
import shap
import pandas as pd
import matplotlib.pyplot as plt

# For tree-based models (fast)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)  # shape: (n_samples, n_features)

# For neural nets / any model (slower)
# explainer = shap.KernelExplainer(model.predict, shap.sample(X_train, 100))
# shap_values = explainer.shap_values(X_test[:50])

mean_shap = pd.Series(
    abs(shap_values).mean(axis=0),
    index=feature_names,
).sort_values(ascending=False)

print("Mean |SHAP| feature importance:")
print(mean_shap.head(10))

shap.summary_plot(shap_values, X_test, feature_names=feature_names)
```
