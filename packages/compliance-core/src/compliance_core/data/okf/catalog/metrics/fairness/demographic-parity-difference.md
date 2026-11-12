---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Demographic Parity Difference
description: Difference in positive prediction rates between the most and least favoured group. Zero indicates equal positive prediction rates across all groups.
tags: [metric, fairness, demographic-parity, group-fairness, eu-ai-act, fairlearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 10 requires training data to be examined for biases. Demographic parity difference measures whether a model assigns positive outcomes equally across groups. A value of 0 is ideal; |value| ≤ 0.05 is a common acceptance threshold.

**Applies to**: Model, ModelService | **Sources**: Fairlearn; AI Fairness 360; EU AI Act Art. 10
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)
- [GDPR Art. 22](../../requirements/gdpr/art22-automated-decisions.md)

# Instance

```json
{
  "id": "metric-demographic-parity-difference",
  "name": "Demographic Parity Difference",
  "description": "Difference in positive prediction rates between the most and least favoured grou",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ", "name": "rate difference" },
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
from fairlearn.metrics import demographic_parity_difference

# y_true: ground-truth labels; y_pred: model predictions
# sensitive_features: protected attribute column (e.g. gender, race)
dpd = demographic_parity_difference(
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive_features,
)
print(f"Demographic Parity Difference: {dpd:.4f}")
# Threshold guidance: |dpd| <= 0.05 (strict), <= 0.10 (moderate)
```
