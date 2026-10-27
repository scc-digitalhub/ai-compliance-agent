---
type: Metric
title: Software Carbon Intensity (SCI)
description: Carbon emissions per functional unit of software execution: SCI = (E × I + M) / R. Standardised by the Green Software Foundation (GSF SCI v1.0).
tags: [metric, environmental, sci, green-software, carbon-intensity, gsf]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The Green Software Foundation SCI (ISO/IEC 21031:2024 candidate) provides a standardised, functional-unit-based carbon metric applicable to AI inference services. Unlike absolute emissions, SCI enables comparison across different-scale deployments and tracks efficiency improvements over model versions.

**Applies to**: ModelService, Operation | **Sources**: Green Software Foundation SCI v1.0; ISO/IEC 21031:2024


# Instance

```json
{
  "id": "metric-software-carbon-intensity",
  "name": "Software Carbon Intensity (SCI)",
  "description": "Carbon emissions per functional unit of software execution: SCI = (E × I + M) / ",
  "kind": "PRIMITIVE",
  "scale": "RATIO",
  "unit": { "symbol": "gCO₂e / R", "name": "grams CO2e per functional unit" },
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
# SCI = (E * I + M) / R
# E = energy consumed (kWh), I = carbon intensity (gCO2e/kWh),
# M = embodied carbon of hardware (gCO2e, amortised), R = functional unit

def compute_sci(
    energy_kwh: float,     # energy consumed during observation period
    carbon_intensity: float,  # grid carbon intensity gCO2e/kWh (from electricitymap.org)
    embodied_carbon_g: float, # amortised hardware carbon over period
    functional_units: int,    # e.g. number of API calls, inferences, users
) -> float:
    operational = energy_kwh * 1000 * carbon_intensity  # convert kWh to Wh, then to gCO2e
    return (operational + embodied_carbon_g) / functional_units

# Example: inference API
sci = compute_sci(
    energy_kwh=0.5,              # 0.5 kWh for 10 000 inferences
    carbon_intensity=233.0,      # Italy avg 2024 (gCO2e/kWh)
    embodied_carbon_g=50.0,      # amortised GPU carbon
    functional_units=10_000,     # inferences
)
print(f"SCI: {sci:.4f} gCO2e per inference")
```
