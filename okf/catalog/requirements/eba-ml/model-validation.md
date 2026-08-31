---
type: Requirement
title: EBA ML — Independent Model Validation
description: ML models used in credit risk must undergo independent validation covering conceptual soundness, data quality, performance stability, and ongoing monitoring.
tags: ["eba", "banking", "model-validation", "credit-risk", "finance"]
schema: ../../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-eba-model_validation",
  "name": "EBA ML — Independent Model Validation",
  "description": "Mandates independent validation of credit ML models across data quality, performance stability, demographic consistency, and ongoing monitoring.",
  "source": {{
    "framework": "EBA_ML_GUIDELINES",
    "article": "§ 4.2",
    "version": "2023",
    "uri": "https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-report-machine-learning-credit-risk"
  }},
  "requirement_text": "Institutions should ensure that ML models used in credit risk are subject to independent model validation covering: conc...",
  "summary": "Mandates independent validation of credit ML models across data quality, performance stability, demographic consistency, and ongoing monitoring.",
  "kind": "TESTING",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Institutions should ensure that ML models used in credit risk are subject to independent model validation covering: conceptual soundness of the modelling approach; quality and representativeness of training and validation data; model performance on hold-out and out-of-time samples; stability of performance across demographic segments; ongoing performance monitoring and backtesting; and assessment of model limitations and assumptions.

# Related Concepts

- [EBA ML RegulatoryRef](../../regulatory-refs/eba-ml-guidelines.md)
- [AttributeRef: Creditworthiness Score](../../attributes/creditworthiness-score.md)
