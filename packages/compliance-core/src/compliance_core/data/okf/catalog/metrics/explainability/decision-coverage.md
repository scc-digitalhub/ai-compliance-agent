---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Decision Coverage (Traceable Predictions)
description: Fraction of model predictions for which a traceable decision path or rule-based explanation can be generated. Measures explainability completeness across the prediction space.
tags: [metric, explainability, coverage, traceability, ieee-7001, eu-hleg-altai]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

IEEE 7001-2021 defines transparency as a measurable property. Decision coverage tracks what fraction of predictions can be explained (via rule extraction, decision trees, or other means). EU AI Act Art. 14 requires the model to be interpretable enough for human overseers to correctly interpret outputs.

**Applies to**: Model | **Sources**: IEEE 7001-2021; EU HLEG ALTAI 2020; EU AI Act Art. 14
- [EU AI Act Art. 14](../../requirements/eu-ai-act/art14-human-oversight.md)

# Instance

```json
{
  "id": "metric-decision-coverage",
  "name": "Decision Coverage (Traceable Predictions)",
  "description": "Fraction of model predictions for which a traceable decision path or rule-based ",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "%", "name": "percent" },
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
from sklearn.tree import DecisionTreeClassifier
import numpy as np

# Approach: fit a surrogate decision tree to model predictions
# Coverage = fraction of test instances whose leaf has >= min_samples
surrogate = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10)
surrogate.fit(X_train, model.predict(X_train))

# Get leaf indices for test set
leaf_ids = surrogate.apply(X_test)
leaf_sizes = np.bincount(surrogate.apply(X_train))

min_leaf_size = 10  # explanations covering < 10 training samples are unreliable
traceable_mask = leaf_sizes[leaf_ids] >= min_leaf_size
coverage = traceable_mask.mean()
print(f"Decision Coverage: {coverage:.4f}")
print(f"Surrogate fidelity: {np.mean(surrogate.predict(X_test) == model.predict(X_test)):.4f}")
```
