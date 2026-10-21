---
type: Requirement
title: EBA ML — Explainability for Credit Decisions
description: ML models driving credit decisions must provide individual-level explanations that are understandable to the affected person and meet GDPR Art. 22 meaningful information requirements.
tags: ["eba", "banking", "explainability", "credit-decision", "gdpr-art22", "finance"]
schema: ../../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-eba-ml_explainability",
  "name": "EBA ML — Explainability for Credit Decisions",
  "description": "Requires GDPR Art. 22-compliant individual and global explanations for ML-driven credit decisions, expressed in applicant-understandable terms.",
  "source": {{
    "framework": "EBA_ML_GUIDELINES",
    "article": "§ 4.5",
    "version": "2023",
    "uri": "https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-report-machine-learning-credit-risk"
  }},
  "requirement_text": "Institutions using ML models for credit decisions should be able to provide meaningful explanations to data subjects in accordance with GDPR Article 22. Explanations should identify the most influential factors in the decision, be expressed in terms understandable to the applicant, be consistent and reproducible, and be subject to quality controls. Both global model explanations and local (individual) explanations should be available.",
  "summary": "Requires GDPR Art. 22-compliant individual and global explanations for ML-driven credit decisions, expressed in applicant-understandable terms.",
  "kind": "TRANSPARENCY",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Institutions using ML models for credit decisions should be able to provide meaningful explanations to data subjects in accordance with GDPR Article 22. Explanations should identify the most influential factors in the decision, be expressed in terms understandable to the applicant, be consistent and reproducible, and be subject to quality controls. Both global model explanations and local (individual) explanations should be available.

# Related Concepts

- [EBA ML RegulatoryRef](../../regulatory-refs/eba-ml-guidelines.md)
- [AttributeRef: Creditworthiness Score](../../attributes/creditworthiness-score.md)
