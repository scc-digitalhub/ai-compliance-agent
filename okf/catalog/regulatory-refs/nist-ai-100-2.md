---
type: RegulatoryRef
title: NIST AI 100-2 Adversarial ML Taxonomy
description: NIST AI 100-2 (2024) — Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations, providing a standardised classification of AI adversarial threats.
tags: [standard, nist, adversarial-ml, taxonomy, attacks, mitigations, international]
schema: ../../okb/schemas/RegulatoryRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 provides a standardised taxonomy for adversarial machine learning
attacks and mitigations. It is directly referenced in cybersecurity requirements
for AI systems under EU AI Act Art. 15 and supports the security requirements
of NIS2 Art. 21 for AI components of essential services.

# Instance

```json
{
  "framework": "NIST_AI_100_2",
  "version": "2024",
  "uri": "https://doi.org/10.6028/NIST.AI.100-2e2023"
}
```

# Attack Categories

| Category | Attacks |
|----------|---------|
| Evasion | Adversarial examples at inference time |
| Poisoning | Training data manipulation (availability, backdoor) |
| Privacy | Membership inference, training data extraction, model inversion |
| Abuse | Prompt injection, jailbreak, indirect injection |
