---
type: MisuseScenario
title: Model Inversion Attack
description: An adversary uses model outputs to reconstruct representative or actual training samples, potentially recovering sensitive features (e.g. medical images, faces) associated with training data subjects.
tags: ["misuse", "model-inversion", "privacy", "adversarial", "nist-ai-100-2", "sensitive-data"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 §4.3. Particularly severe for models trained on GDPR Art. 9 special-category data (medical imaging, biometric systems). Violates purpose limitation and storage limitation principles under GDPR Art. 5.

# Instance

```json
{{
  "id": "misuse-model_inversion",
  "name": "Model Inversion Attack",
  "description": "An adversary uses model outputs to reconstruct representative or actual training samples, potentiall",
  "misuse_kind": "DATA_LEAKAGE",
  "intentionality": "ADVERSARIAL",
  "likelihood": "UNLIKELY",
  "impact": "CRITICAL",
  "actor_roles": ["END_USER"],
  "rationale": "NIST AI 100-2 §4.3. Particularly severe for models trained on GDPR Art. 9 special-category data (med"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [NIST AI 100-2](../regulatory-refs/nist-ai-100-2.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
