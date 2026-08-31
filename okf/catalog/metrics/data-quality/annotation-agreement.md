---
type: Metric
title: Annotation Agreement — Cohen's κ
description: Inter-annotator agreement coefficient corrected for chance. κ = 1 means perfect agreement; κ = 0 means agreement at chance level.
tags: [metric, data-quality, annotation, inter-rater, cohens-kappa, label-quality]
schema: ../../../okb/schemas/Metric.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Low annotator agreement indicates ambiguous or unreliable labels, which directly degrades model quality and fairness. EU AI Act Art. 10 requires datasets to be 'free of errors to the best extent possible'. Cohen's κ is the standard metric for subjective annotation tasks (sentiment, toxicity, medical imaging).

**Applies to**: Dataset | **Sources**: Cohen 1960; Croissant dataset card standard; EU AI Act Art. 10
- [EU AI Act Art. 10](../../requirements/eu-ai-act/art10-data-governance.md)

# Instance

```json
{
  "id": "metric-annotation-agreement-kappa",
  "name": "Annotation Agreement — Cohen's κ",
  "description": "Inter-annotator agreement coefficient corrected for chance. κ = 1 means perfect ",
  "kind": "PRIMITIVE",
  "scale": "ORDINAL",
  "unit": { "symbol": "κ", "name": "kappa" },
  "range": {
    "lower": -1.0,
    "upper": 1.0,
    "discrete": false,
    "categories": null
  }
}
```

# Computation

```python
from sklearn.metrics import cohen_kappa_score

# annotations_1, annotations_2: arrays of labels from two annotators
kappa = cohen_kappa_score(annotations_1, annotations_2)
print(f"Cohen's κ: {kappa:.4f}")
# Interpretation: < 0.20 slight, 0.20-0.40 fair, 0.41-0.60 moderate,
#                 0.61-0.80 substantial, > 0.80 almost perfect

# For multi-annotator datasets, use Krippendorff's alpha:
import krippendorff
alpha = krippendorff.alpha(reliability_data=annotations_matrix, level_of_measurement='nominal')
print(f"Krippendorff's α: {alpha:.4f}")
```
