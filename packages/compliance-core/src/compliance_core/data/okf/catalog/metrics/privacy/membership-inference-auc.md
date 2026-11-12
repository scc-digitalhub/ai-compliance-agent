---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Membership Inference Attack AUC
description: AUC of a membership inference attack classifier distinguishing training members from non-members. AUC = 0.5 means no privacy leakage; higher means model memorises training data.
tags: [metric, privacy, membership-inference, privacy-audit, nist-ai-100-2, gdpr]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 §4.3 identifies membership inference as a primary privacy attack. AUC = 0.5 means the attack is no better than random (strong privacy); AUC → 1.0 means the model memorises training data (severe privacy leak). GDPR Art. 5(1)(f) requires appropriate security; this metric operationalises that requirement for ML models.

**Applies to**: Model | **Sources**: Shokri et al. 2017; NIST AI 100-2; GDPR Art. 5
- [GDPR Art. 5](../../requirements/gdpr/art5-principles.md)
- [Membership Inference MisuseScenario](../../misuse-scenarios/membership-inference.md)

# Instance

```json
{
  "id": "metric-membership-inference-auc",
  "name": "Membership Inference Attack AUC",
  "description": "AUC of a membership inference attack classifier distinguishing training members ",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "AUC", "name": "area" },
  "range": {
    "lower": 0.5,
    "upper": 1.0,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

# Shadow model approach (Shokri et al. 2017)
# Collect loss/confidence features for member (train) and non-member (test) records

def get_loss_features(model, X, y):
    """Get per-sample loss and top-k confidence features for MI attack."""    import torch, torch.nn.functional as F
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(X, dtype=torch.float32))
        probs = F.softmax(logits, dim=-1).numpy()
    losses = -np.log(probs[np.arange(len(y)), y] + 1e-8)
    return np.column_stack([losses, probs.max(axis=1), probs.min(axis=1)])

feat_train = get_loss_features(model, X_train[:500], y_train[:500])
feat_test  = get_loss_features(model, X_test[:500],  y_test[:500])

X_attack = np.vstack([feat_train, feat_test])
y_attack = np.hstack([np.ones(len(feat_train)), np.zeros(len(feat_test))])

attacker = LogisticRegression().fit(X_attack, y_attack)
mi_auc = roc_auc_score(y_attack, attacker.predict_proba(X_attack)[:, 1])
print(f"Membership Inference Attack AUC: {mi_auc:.4f}")
# AUC > 0.6 warrants investigation; > 0.7 requires privacy mitigations
```
