---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: LIME Local Fidelity Score
description: R² of the local linear surrogate fitted by LIME around a single prediction. Values close to 1 mean the surrogate accurately represents the model locally.
tags: [metric, explainability, lime, local-fidelity, surrogate, transparency]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

LIME builds a local interpretable surrogate model around each prediction. The local fidelity R² quantifies how well the surrogate explains the model in the neighbourhood of the instance. Low fidelity means the explanation may be misleading. EU AI Act Art. 13 requires explanations to enable deployers to correctly interpret outputs.

**Applies to**: Model | **Sources**: Ribeiro et al. 2016; EU AI Act Art. 13
- [EU AI Act Art. 13](../../requirements/eu-ai-act/art13-transparency.md)

# Instance

```json
{
  "id": "metric-lime-local-fidelity",
  "name": "LIME Local Fidelity Score",
  "description": "R² of the local linear surrogate fitted by LIME around a single prediction. Valu",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "R²", "name": "coefficient of determination" },
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
from lime.lime_tabular import LimeTabularExplainer
import numpy as np

explainer = LimeTabularExplainer(
    training_data=X_train,
    feature_names=feature_names,
    class_names=class_names,
    mode="classification",
)

# Compute local fidelity for a batch of test instances
fidelity_scores = []
for i in range(min(100, len(X_test))):
    exp = explainer.explain_instance(
        X_test[i],
        model.predict_proba,
        num_features=10,
    )
    fidelity_scores.append(exp.score)  # R² of local surrogate

mean_fidelity = np.mean(fidelity_scores)
print(f"Mean LIME local fidelity R²: {mean_fidelity:.4f}")
# R² < 0.7 suggests complex local non-linearity; explanations may be unreliable
```
