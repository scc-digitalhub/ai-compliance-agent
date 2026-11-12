---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Brier Score
description: Mean squared difference between predicted probability and true binary outcome. Combines discrimination and calibration. Perfect score = 0; random binary classifier = 0.25.
tags: [metric, calibration, brier-score, probabilistic, discrimination, sklearn]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The Brier score jointly rewards calibration and discrimination, making it a comprehensive single metric for probabilistic classifiers. It is particularly useful for risk scoring models (credit, health, criminal justice) where the probability output is used directly, not just the binary prediction.

**Applies to**: Model | **Sources**: Brier 1950; sklearn; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-brier-score",
  "name": "Brier Score",
  "description": "Mean squared difference between predicted probability and true binary outcome. C",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "BS", "name": "mean squared error" },
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
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(y_true, y_prob)
print(f"Brier Score: {brier:.4f}")
# Baseline (always predict prevalence p): p*(1-p) ≈ 0.25 for balanced binary
# Skill score (relative improvement over baseline):
p_bar = y_true.mean()
brier_ref = p_bar * (1 - p_bar)
brier_skill = 1 - brier / brier_ref
print(f"Brier Skill Score: {brier_skill:.4f}")
# Brier skill > 0.25 indicates meaningful probabilistic accuracy
```
