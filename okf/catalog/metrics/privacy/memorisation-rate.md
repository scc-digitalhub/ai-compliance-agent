---
type: Metric
title: Training Data Memorisation Rate
description: Fraction of training samples that can be approximately reconstructed or triggered verbatim from the model. Specifically relevant for LLMs and generative models.
tags: [metric, privacy, memorisation, data-extraction, llm, nist-ai-100-2, gdpr]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 §4.3 identifies training data extraction as a privacy attack. For LLMs, memorisation is measured as the fraction of training sequences a model can regenerate verbatim when prompted with a prefix. GDPR Art. 17 (right to erasure) cannot be satisfied if training data is memorised in model weights.

**Applies to**: Model | **Sources**: Carlini et al. 2021, 2023; NIST AI 100-2; GDPR Art. 17
- [GDPR Art. 5](../../requirements/gdpr/art5-principles.md)
- [Training Data Extraction MisuseScenario](../../misuse-scenarios/training-data-extraction.md)

# Instance

```json
{
  "id": "metric-memorisation-rate",
  "name": "Training Data Memorisation Rate",
  "description": "Fraction of training samples that can be approximately reconstructed or triggere",
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
import torch
import numpy as np

def memorisation_rate(
    model,
    tokenizer,
    training_samples: list[str],
    prefix_len: int = 50,
    generation_len: int = 50,
    threshold: float = 0.9,
) -> float:
    """
    For each training sample, prompt the model with the first `prefix_len` tokens
    and check if the generated continuation reproduces >= threshold fraction of the
    original next `generation_len` tokens.
    """
    memorised = 0
    for sample in training_samples:
        tokens = tokenizer.encode(sample)
        if len(tokens) < prefix_len + generation_len:
            continue
        prefix = tokens[:prefix_len]
        target = tokens[prefix_len:prefix_len + generation_len]
        with torch.no_grad():
            generated = model.generate(
                torch.tensor([prefix]),
                max_new_tokens=generation_len,
                do_sample=False,
            )[0][prefix_len:].tolist()
        overlap = sum(a == b for a, b in zip(generated, target)) / generation_len
        if overlap >= threshold:
            memorised += 1
    return memorised / len(training_samples)

rate = memorisation_rate(model, tokenizer, training_samples[:200])
print(f"Memorisation rate (threshold=0.9): {rate:.4f}")
```
