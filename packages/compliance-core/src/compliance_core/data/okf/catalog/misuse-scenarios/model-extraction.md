---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Model Extraction / Theft
description: An adversary systematically queries an AI system to reconstruct a functionally equivalent model, stealing intellectual property and enabling subsequent adversarial attacks.
tags: ["misuse", "model-extraction", "adversarial", "ip-theft", "cybersecurity"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 15 requires cybersecurity measures including protection against model integrity attacks. Extracted models can be used for membership inference attacks or to craft targeted adversarial examples against the original.

# Instance

```json
{{
  "id": "misuse-model_extraction",
  "name": "Model Extraction / Theft",
  "description": "An adversary systematically queries an AI system to reconstruct a functionally equivalent model, ste",
  "misuse_kind": "MODEL_EXTRACTION",
  "intentionality": "ADVERSARIAL",
  "likelihood": "UNLIKELY",
  "impact": "HIGH",
  "actor_roles": ["END_USER"],
  "rationale": "EU AI Act Art. 15 requires cybersecurity measures including protection against model integrity attac"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
