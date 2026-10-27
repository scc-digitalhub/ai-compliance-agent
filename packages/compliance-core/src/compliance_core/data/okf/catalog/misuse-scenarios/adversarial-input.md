---
type: MisuseScenario
title: Adversarial Input Attack
description: Carefully crafted perturbations to inputs cause an AI system to misclassify or produce attacker-controlled outputs, potentially evading safety classifiers or fraud detectors.
tags: ["misuse", "adversarial-input", "adversarial-ml", "evasion", "cybersecurity"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 explicitly requires resilience against adversarial inputs attempting to alter the output. Critical in security-sensitive applications: fraud detection, content moderation, biometric authentication.

# Instance

```json
{{
  "id": "misuse-adversarial_input",
  "name": "Adversarial Input Attack",
  "description": "Carefully crafted perturbations to inputs cause an AI system to misclassify or produce attacker-cont",
  "misuse_kind": "ADVERSARIAL_INPUT",
  "intentionality": "ADVERSARIAL",
  "likelihood": "POSSIBLE",
  "impact": "HIGH",
  "actor_roles": ["END_USER"],
  "rationale": "EU AI Act Art. 15 explicitly requires resilience against adversarial inputs attempting to alter the "
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
