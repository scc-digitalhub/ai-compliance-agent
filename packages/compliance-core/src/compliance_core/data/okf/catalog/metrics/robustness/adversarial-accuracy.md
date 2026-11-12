---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: Adversarial Accuracy
description: Model accuracy on adversarially perturbed inputs. Measures how much accuracy degrades under attack compared to clean inputs.
tags: [metric, robustness, adversarial, attack, nist-ai-100-2, eu-ai-act-art15]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 requires AI to be resilient against manipulation by third parties, including adversarial inputs. NIST AI 100-2 classifies adversarial examples as the primary evasion attack vector. Adversarial accuracy is measured under specific attack budgets (ε in Lp-norm).

**Applies to**: Model, ModelService | **Sources**: NIST AI 100-2; EU AI Act Art. 15; IBM ART library
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)
- [Adversarial Input MisuseScenario](../../misuse-scenarios/adversarial-input.md)

# Instance

```json
{
  "id": "metric-adversarial-accuracy",
  "name": "Adversarial Accuracy",
  "description": "Model accuracy on adversarially perturbed inputs. Measures how much accuracy deg",
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
# Using IBM Adversarial Robustness Toolbox (ART)
from art.attacks.evasion import ProjectedGradientDescent
from art.estimators.classification import PyTorchClassifier
import numpy as np

classifier = PyTorchClassifier(
    model=model, loss=criterion,
    input_shape=input_shape, nb_classes=nb_classes,
)
attack = ProjectedGradientDescent(
    estimator=classifier,
    eps=0.03,           # L∞ perturbation budget (e.g. 8/255 for images)
    eps_step=0.007,
    max_iter=40,
    targeted=False,
)
x_adv = attack.generate(x=X_test)

adv_acc = np.mean(
    np.argmax(classifier.predict(x_adv), axis=1) == y_test
)
clean_acc = np.mean(
    np.argmax(classifier.predict(X_test), axis=1) == y_test
)
print(f"Clean Accuracy: {clean_acc:.4f}  Adversarial Accuracy: {adv_acc:.4f}")
print(f"Accuracy Drop: {clean_acc - adv_acc:.4f}")
```
