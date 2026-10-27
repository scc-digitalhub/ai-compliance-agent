---
type: Metric
title: Energy per Inference
description: Average energy (in Wh or mWh) consumed by the model to process a single inference request. Lower is better for sustainable deployment.
tags: [metric, environmental, energy, inference-efficiency, green-ai, codecarbon]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Energy per inference is the operational efficiency metric for deployed AI services. EU AI Act Art. 15 requires AI to achieve the intended purpose with appropriate resource use. ModelService operators tracking this metric can optimise model compression, batching, and hardware selection.

**Applies to**: ModelService | **Sources**: CodeCarbon; Green Software Foundation; EU AI Act Art. 15
- [EU AI Act Art. 15](../../requirements/eu-ai-act/art15-accuracy-robustness.md)

# Instance

```json
{
  "id": "metric-energy-per-inference",
  "name": "Energy per Inference",
  "description": "Average energy (in Wh or mWh) consumed by the model to process a single inferenc",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "Wh", "name": "watt-hours" },
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
import time
from codecarbon import EmissionsTracker

def measure_energy_per_inference(model, X_sample, n_repeats=100):
    tracker = EmissionsTracker(save_to_file=False)
    tracker.start()
    t0 = time.perf_counter()
    for _ in range(n_repeats):
        _ = model.predict(X_sample)
    elapsed = time.perf_counter() - t0
    emissions_kg = tracker.stop()
    energy_kwh = emissions_kg / 0.233  # approx. reverse using Italian carbon intensity
    energy_wh_per_inference = energy_kwh * 1000 / n_repeats
    ms_per_inference = elapsed * 1000 / n_repeats
    print(f"Energy per inference: {energy_wh_per_inference*1000:.4f} mWh")
    print(f"Latency per inference: {ms_per_inference:.2f} ms")
    return energy_wh_per_inference
```
