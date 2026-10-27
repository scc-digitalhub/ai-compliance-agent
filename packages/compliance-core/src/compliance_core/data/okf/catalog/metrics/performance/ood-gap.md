---
type: Metric
title: Out-of-Distribution (OOD) Performance Gap
description: Absolute difference in a chosen performance metric (e.g. F1) between in-distribution (IID) test set and out-of-distribution (OOD) test set. Measures robustness to distribution shift.
tags: [metric, performance, ood, distribution-shift, robustness, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 requires AI to 'perform consistently throughout its lifecycle'. Distribution shift between training/validation data and real deployment is a leading cause of performance degradation. The OOD gap quantifies this risk and should be part of the risk management system (Art. 9).

**Applies to**: Model | **Sources**: EU AI Act Art. 15; EU AI Act Art. 9; NIST AI RMF MS-2
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)
- [EU AI Act Art. 9](../../requirements/eu-ai-act/art9-risk-management.md)

# Instance

```json
{
  "id": "metric-ood-performance-gap",
  "name": "Out-of-Distribution (OOD) Performance Gap",
  "description": "Absolute difference in a chosen performance metric (e.g. F1) between in-distribu",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "Δ%", "name": "metric difference" },
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
from sklearn.metrics import f1_score

# iid_test: in-distribution hold-out; ood_test: distribution-shifted test set
f1_iid = f1_score(y_true_iid, y_pred_iid, average="macro")
f1_ood = f1_score(y_true_ood, y_pred_ood, average="macro")
ood_gap = abs(f1_iid - f1_ood)

print(f"F1 IID: {f1_iid:.4f}  F1 OOD: {f1_ood:.4f}")
print(f"OOD Performance Gap: {ood_gap:.4f}")
# Gap > 0.05 warrants investigation; > 0.10 is a red flag for deployment
```
