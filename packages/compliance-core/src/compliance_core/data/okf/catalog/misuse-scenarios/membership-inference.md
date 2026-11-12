---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Membership Inference Attack
description: An adversary queries a trained model to determine whether a specific data record was used in training, violating data subjects' right not to have their inclusion in a training dataset revealed.
tags: ["misuse", "membership-inference", "privacy", "adversarial", "nist-ai-100-2", "gdpr"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 §4.3. GDPR Art. 5 (data minimisation) and Art. 17 (right to erasure) are undermined if model parameters memorise training data. Particularly severe for models trained on medical or criminal justice datasets.

# Instance

```json
{{
  "id": "misuse-membership_inference",
  "name": "Membership Inference Attack",
  "description": "An adversary queries a trained model to determine whether a specific data record was used in trainin",
  "misuse_kind": "DATA_LEAKAGE",
  "intentionality": "ADVERSARIAL",
  "likelihood": "POSSIBLE",
  "impact": "HIGH",
  "actor_roles": ["END_USER"],
  "rationale": "NIST AI 100-2 §4.3. GDPR Art. 5 (data minimisation) and Art. 17 (right to erasure) are undermined if"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [NIST AI 100-2](../regulatory-refs/nist-ai-100-2.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
