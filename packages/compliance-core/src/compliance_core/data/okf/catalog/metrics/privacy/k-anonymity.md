---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: k-Anonymity
description: Minimum number of records that share the same quasi-identifier combination. k = 1 means a record is uniquely identifiable; higher k means lower re-identification risk.
tags: [metric, privacy, k-anonymity, re-identification, de-identification, nist-sp-800-188]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

k-anonymity (Samarati & Sweeney 1998) is the baseline standard for de-identified datasets. NIST SP 800-188 uses k-anonymity as a primary de-identification metric. GDPR Art. 4(5) pseudonymisation and Art. 89 research exemptions implicitly require k ≥ 5. EU AI Act Art. 10 data governance may require anonymisation of sensitive training data.

**Applies to**: Dataset | **Sources**: Samarati & Sweeney 1998; NIST SP 800-188; GDPR Art. 4(5)
- [GDPR Art. 5](../../requirements/gdpr/art5-principles.md)
- [GDPR Art. 25](../../requirements/gdpr/art25-privacy-by-design.md)

# Instance

```json
{
  "id": "metric-k-anonymity",
  "name": "k-Anonymity",
  "description": "Minimum number of records that share the same quasi-identifier combination. k = ",
  "kind": "PRIMITIVE",
  "scale": "ORDINAL",
  "unit": { "symbol": "k", "name": "equivalence class size" },
  "range": {
    "lower": 1,
    "upper": null,
    "discrete": true,
    "categories": null
  }
}
```

# Computation

```python
import pandas as pd

def k_anonymity(df: pd.DataFrame, quasi_identifiers: list) -> int:
    """Returns the minimum equivalence class size (k) over all QI combinations."""    group_sizes = df.groupby(quasi_identifiers).size()
    return int(group_sizes.min())

# Quasi-identifiers: attributes that could be combined to re-identify individuals
quasi_ids = ["age_band", "postcode_prefix", "gender", "ethnicity_group"]
k = k_anonymity(df, quasi_ids)
print(f"k-anonymity: {k}")
# k < 5 requires suppression or generalisation before sharing
# k < 2 means unique records exist — high re-identification risk

# Distribution of equivalence class sizes:
print(df.groupby(quasi_ids).size().describe())
```
