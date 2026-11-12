---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: CO₂ Equivalent Emissions
description: Total CO₂-equivalent greenhouse gas emissions (kgCO₂e) produced by training or operating an AI model. Accounts for hardware energy consumption and regional grid carbon intensity.
tags: [metric, environmental, co2, emissions, sustainability, codecarbon, green-ai, unesco]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

UNESCO AI Ethics Recommendation (§4.8) requires AI to be environmentally sustainable. Training large AI models can emit hundreds of tonnes of CO₂e. EU Green Deal and Corporate Sustainability Reporting Directive (CSRD) increasingly require ICT carbon reporting. The ML CO2 Impact tool by Lacoste et al. (2019) is the standard instrument.

**Applies to**: Model, Operation | **Sources**: Lacoste et al. 2019; CodeCarbon; UNESCO AI Ethics §4.8; CSRD
- [UNESCO AI Ethics — Proportionality](../../requirements/unesco/proportionality.md)

# Instance

```json
{
  "id": "metric-co2-equivalent",
  "name": "CO₂ Equivalent Emissions",
  "description": "Total CO₂-equivalent greenhouse gas emissions (kgCO₂e) produced by training or o",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "kgCO₂e", "name": "kilograms CO2 equivalent" },
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
from codecarbon import EmissionsTracker

# Track training emissions
tracker = EmissionsTracker(
    project_name="model_training",
    output_dir="./emissions_logs",
    country_iso_code="ITA",   # Italy — high renewables mix
)
tracker.start()

# --- training loop ---
train_model(model, train_loader, n_epochs=10)
# ---------------------

emissions = tracker.stop()  # returns kgCO2e
print(f"Training emissions: {emissions:.4f} kgCO2e")

# For inference, wrap the prediction loop:
tracker_inf = EmissionsTracker()
tracker_inf.start()
predictions = model.predict(X_test)
inf_emissions = tracker_inf.stop()
print(f"Inference emissions (test set): {inf_emissions*1000:.4f} gCO2e")
```
