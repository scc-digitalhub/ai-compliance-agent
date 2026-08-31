---
type: Metric
title: Dataset Completeness
description: Fraction of required values that are present (non-null) in the dataset. A value of 1.0 means no missing values.
tags: [metric, data-quality, completeness, missing-values, iso-8000, eu-ai-act]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

ISO 8000 defines completeness as a core data quality dimension. EU AI Act Art. 10 requires training datasets to be 'complete with regard to the intended purpose'. Incompleteness can introduce systematic bias if missingness is correlated with protected attributes.

**Applies to**: Dataset | **Sources**: ISO 8000; EU AI Act Art. 10; DAMA DMBOK
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)
- [ISO/IEC 42001 A.7.2](../../requirements/iso-42001-annex-a/a72-data-acquisition.md)

# Instance

```json
{
  "id": "metric-data-completeness",
  "name": "Dataset Completeness",
  "description": "Fraction of required values that are present (non-null) in the dataset. A value ",
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
import pandas as pd

def completeness(df: pd.DataFrame) -> pd.Series:
    """Per-column completeness (fraction of non-null values)."""
    return 1.0 - df.isnull().mean()

col_completeness = completeness(df)
overall = col_completeness.mean()
print(f"Overall completeness: {overall:.4f}")
print(col_completeness.sort_values())

# Completeness by group (detect differential missingness)
for group, subset in df.groupby("protected_attr"):
    print(f"  Group {group}: {completeness(subset).mean():.4f}")
```
