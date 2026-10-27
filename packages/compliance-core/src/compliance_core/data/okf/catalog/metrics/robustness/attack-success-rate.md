---
type: Metric
title: Attack Success Rate
description: Fraction of adversarial inputs that successfully cause a model misclassification or targeted output. Complement of adversarial accuracy.
tags: [metric, robustness, attack-success, adversarial, nist-ai-100-2, red-team]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 uses attack success rate as the primary measurement for evasion, poisoning, and prompt injection attacks. EU AI Act Art. 15 implies this metric through the 'resilience against manipulation by third parties' requirement. Red-team exercises should report this metric.

**Applies to**: Model, ModelService | **Sources**: NIST AI 100-2; EU AI Act Art. 15; OWASP LLM Top 10
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)
- [Prompt Injection MisuseScenario](../../misuse-scenarios/prompt-injection.md)

# Instance

```json
{
  "id": "metric-attack-success-rate",
  "name": "Attack Success Rate",
  "description": "Fraction of adversarial inputs that successfully cause a model misclassification",
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
import numpy as np

def attack_success_rate(y_clean_pred, y_adv_pred, y_true=None, targeted=False, target_class=None):
    """
    Untargeted: fraction where adversarial prediction differs from clean prediction.
    Targeted: fraction where adversarial prediction equals target_class.
    """
    if targeted:
        return np.mean(y_adv_pred == target_class)
    else:
        # Misclassification rate (not necessarily from correct clean pred)
        if y_true is not None:
            originally_correct = y_clean_pred == y_true
            return np.mean(y_adv_pred[originally_correct] != y_true[originally_correct])
        return np.mean(y_adv_pred != y_clean_pred)

# For LLMs (prompt injection), measure via string matching on output
def prompt_injection_success_rate(outputs, injected_marker="INJECTED_PAYLOAD"):
    return sum(injected_marker in o for o in outputs) / len(outputs)
```
