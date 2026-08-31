---
type: Metric
title: Theil Index (Between-group)
description: Information-theoretic inequality measure of benefit distribution across demographic groups. Zero means perfectly equal benefit distribution.
tags: [metric, fairness, theil-index, inequality, individual-fairness, aif360]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The Theil index measures overall inequality in model benefit distribution, capturing both between-group and within-group disparities. Unlike pairwise metrics it evaluates fairness across the full population simultaneously. Useful for multi-class protected attributes.

**Applies to**: Model, Dataset | **Sources**: AI Fairness 360; Speicher et al. 2018; ISO/IEC TR 24027


# Instance

```json
{
  "id": "metric-theil-index",
  "name": "Theil Index (Between-group)",
  "description": "Information-theoretic inequality measure of benefit distribution across demograp",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "T", "name": "nats" },
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
from aif360.metrics import ClassificationMetric

# Using AIF360 classification metric (see make_aif360_dataset above)
metric = ClassificationMetric(
    ds_true, ds_pred,
    unprivileged_groups=[{"protected": 0}],
    privileged_groups=[{"protected": 1}],
)
theil = metric.between_group_theil_index()
print(f"Between-group Theil Index: {theil:.4f}")
# Theil index > 0.1 signals substantial inequality
```
