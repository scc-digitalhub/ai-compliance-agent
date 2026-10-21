---
type: Requirement
title: EBA ML — Demographic Bias Testing in Credit Scoring
description: Institutions must test ML credit scoring models for demographic bias across protected characteristics and document bias mitigation measures taken.
tags: ["eba", "banking", "bias", "fairness", "credit-scoring", "finance"]
schema: ../../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-eba-demographic_bias",
  "name": "EBA ML — Demographic Bias Testing in Credit Scoring",
  "description": "Mandates systematic demographic bias testing and documentation of mitigation for ML credit scoring models.",
  "source": {{
    "framework": "EBA_ML_GUIDELINES",
    "article": "§ 4.3",
    "version": "2023",
    "uri": "https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-report-machine-learning-credit-risk"
  }},
  "requirement_text": "Institutions should test ML credit scoring models for potential demographic bias, including disparate impact across groups defined by protected characteristics. Testing should cover: performance metric gaps across demographic segments; proxy discrimination through correlated features; intersectional bias analysis where feasible; and documentation of bias mitigation measures and residual disparities. Results should be disclosed to model validation functions and senior management.",
  "summary": "Mandates systematic demographic bias testing and documentation of mitigation for ML credit scoring models.",
  "kind": "TESTING",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Institutions should test ML credit scoring models for potential demographic bias, including disparate impact across groups defined by protected characteristics. Testing should cover: performance metric gaps across demographic segments; proxy discrimination through correlated features; intersectional bias analysis where feasible; and documentation of bias mitigation measures and residual disparities. Results should be disclosed to model validation functions and senior management.

# Related Concepts

- [EBA ML RegulatoryRef](../../regulatory-refs/eba-ml-guidelines.md)
- [AttributeRef: Creditworthiness Score](../../attributes/creditworthiness-score.md)
