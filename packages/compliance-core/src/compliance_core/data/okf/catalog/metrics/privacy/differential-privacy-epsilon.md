---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Differential Privacy Budget (ε)
description: Privacy budget parameter for (ε, δ)-differential privacy. Smaller ε means stronger privacy guarantee. ε = 0 is perfect privacy; ε ∈ [1, 10] is typical in practice.
tags: [metric, privacy, differential-privacy, epsilon, gdpr, nist-sp-800-188]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Differential privacy (Dwork 2006) provides a mathematically rigorous privacy guarantee: an adversary learns almost nothing about any individual from the model output. GDPR Art. 5(1)(f) (integrity and confidentiality) and Art. 25 (privacy by design) are operationalised through DP. ε ≤ 1 provides strong privacy; ε ≤ 10 is practical for ML.

**Applies to**: Model, Dataset | **Sources**: Dwork et al. 2006; NIST SP 800-188; GDPR Art. 25
- [GDPR Art. 25](../../requirements/gdpr/art25-privacy-by-design.md)
- [UNESCO Privacy](../../requirements/unesco/privacy.md)

# Instance

```json
{
  "id": "metric-differential-privacy-epsilon",
  "name": "Differential Privacy Budget (ε)",
  "description": "Privacy budget parameter for (ε, δ)-differential privacy. Smaller ε means strong",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "ε", "name": "privacy budget" },
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
# Using Google's Differential Privacy for ML (DPoptimizer via Opacus)
from opacus import PrivacyEngine
from opacus.utils.batch_memory_manager import BatchMemoryManager
import torch

privacy_engine = PrivacyEngine()
model, optimiser, train_loader = privacy_engine.make_private_with_epsilon(
    module=model,
    optimizer=optimiser,
    data_loader=train_loader,
    epochs=n_epochs,
    target_epsilon=3.0,   # desired ε
    target_delta=1e-5,    # desired δ (typically 1/n_training_samples)
    max_grad_norm=1.0,
)

# After training, get the actual privacy spent:
epsilon = privacy_engine.get_epsilon(delta=1e-5)
print(f"Privacy spent: ε = {epsilon:.2f} at δ = 1e-5")
```
