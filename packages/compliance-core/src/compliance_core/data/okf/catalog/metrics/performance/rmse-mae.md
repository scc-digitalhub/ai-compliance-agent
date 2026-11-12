---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: RMSE and MAE (Regression Error)
description: Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE) measure prediction error magnitude for regression tasks. RMSE penalises large errors more heavily.
tags: [metric, performance, rmse, mae, regression, sklearn, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 requires 'appropriate levels of accuracy' without prescribing specific metrics — for regression tasks (risk scoring, resource forecasting) RMSE and MAE are the standard accuracy measures. Both must be reported per protected group to detect differential accuracy (EU AI Act Art. 10).

**Applies to**: Model | **Sources**: sklearn; ISO/IEC 25010:2023; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-rmse-mae",
  "name": "RMSE and MAE (Regression Error)",
  "description": "Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE) measure prediction ",
  "kind": "COMPOSITE",
  "scale": "RATIO",
  "unit": { "symbol": "same as target", "name": "target unit" },
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
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

rmse = mean_squared_error(y_true, y_pred, squared=False)
mae  = mean_absolute_error(y_true, y_pred)
print(f"RMSE: {rmse:.4f}  MAE: {mae:.4f}")

# Per-group RMSE (detect differential accuracy)
import pandas as pd
results = pd.DataFrame({"y_true": y_true, "y_pred": y_pred, "group": sensitive_features})
for group, sub in results.groupby("group"):
    g_rmse = mean_squared_error(sub.y_true, sub.y_pred, squared=False)
    print(f"  Group {group} RMSE: {g_rmse:.4f}")
```
