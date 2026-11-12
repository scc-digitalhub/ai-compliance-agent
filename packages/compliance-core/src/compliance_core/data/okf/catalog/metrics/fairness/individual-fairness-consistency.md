---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Individual Fairness — Consistency Score
description: Fraction of individuals whose predicted label matches the majority label of their k-nearest neighbours. High consistency means similar individuals receive similar outcomes.
tags: [metric, fairness, individual-fairness, consistency, knn, aif360]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Individual fairness (Dwork et al. 2012) requires that similar individuals receive similar outcomes. The consistency metric operationalises this by measuring label agreement between an individual and their nearest neighbours in feature space. EU AI Act Art. 10 bias examination implicitly requires this.

**Applies to**: Model | **Sources**: Dwork et al. 2012; AI Fairness 360


# Instance

```json
{
  "id": "metric-individual-fairness-consistency",
  "name": "Individual Fairness — Consistency Score",
  "description": "Fraction of individuals whose predicted label matches the majority label of thei",
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
from aif360.metrics import ClassificationMetric

# Consistency uses k-NN over feature matrix X_test
metric = ClassificationMetric(
    ds_true, ds_pred,
    unprivileged_groups=[{"protected": 0}],
    privileged_groups=[{"protected": 1}],
)
consistency = metric.consistency(n_neighbors=5)
print(f"Individual Fairness Consistency (k=5): {consistency[0]:.4f}")
# Values >= 0.95 indicate high individual fairness
```
