---
type: Requirement
title: EU AI Act Art. 10 — Data Governance and Management
description: Data governance requirements for training, validation, and test datasets: relevance, representativeness, absence of errors, completeness, and examination for biases.
tags: ["eu-ai-act", "high-risk", "data-governance", "bias", "quality"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-10",
  "name": "EU AI Act Art. 10 — Data Governance and Management",
  "description": "Mandates representative, bias-examined, error-free datasets and documented data governance for high-risk AI.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 10",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "Training, validation and testing datasets shall be subject to data governance practices ensuring they are relevant, sufficiently representative, and, to the best extent possible, free of errors and complete with regard to the intended purpose. They shall have the appropriate statistical properties, including as regards the persons or groups of persons on which the high-risk AI system is intended to be used. Datasets shall be examined for possible biases that could affect health and safety or fundamental rights.",
  "summary": "Mandates representative, bias-examined, error-free datasets and documented data governance for high-risk AI.",
  "kind": "DATA_GOVERNANCE",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Training, validation and testing datasets shall be subject to data governance practices ensuring they are relevant, sufficiently representative, and, to the best extent possible, free of errors and complete with regard to the intended purpose. They shall have the appropriate statistical properties, including as regards the persons or groups of persons on which the high-risk AI system is intended to be used. Datasets shall be examined for possible biases that could affect health and safety or fundamental rights.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
