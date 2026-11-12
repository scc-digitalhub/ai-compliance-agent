---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Metric
title: l-Diversity
description: Minimum number of distinct sensitive attribute values within each quasi-identifier equivalence class. Extends k-anonymity to prevent attribute disclosure attacks.
tags: [metric, privacy, l-diversity, attribute-disclosure, de-identification, nist-sp-800-188]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

l-diversity (Machanavajjhala et al. 2007) addresses the weakness of k-anonymity where all k records in an equivalence class share the same sensitive attribute value. NIST SP 800-188 recommends l ≥ 2. Particularly relevant for health and financial data used in AI training.

**Applies to**: Dataset | **Sources**: Machanavajjhala et al. 2007; NIST SP 800-188; GDPR Art. 9
- [GDPR Art. 9](../../requirements/gdpr/art9-special-categories.md)

# Instance

```json
{
  "id": "metric-l-diversity",
  "name": "l-Diversity",
  "description": "Minimum number of distinct sensitive attribute values within each quasi-identifi",
  "kind": "PRIMITIVE",
  "scale": "ORDINAL",
  "unit": { "symbol": "l", "name": "distinct sensitive values" },
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

def l_diversity(
    df: pd.DataFrame,
    quasi_identifiers: list,
    sensitive_attribute: str,
) -> int:
    """Minimum number of distinct sensitive values per QI equivalence class."""    def distinct_values(group):
        return group[sensitive_attribute].nunique()
    group_l = df.groupby(quasi_identifiers).apply(distinct_values)
    return int(group_l.min())

l = l_diversity(df, quasi_identifiers=["age_band", "postcode_prefix"], sensitive_attribute="diagnosis")
print(f"l-diversity: {l}")
# l = 1 means every equivalence class reveals the sensitive attribute
# Recommend l >= 3 for health data, l >= 5 for high-sensitivity contexts
```
