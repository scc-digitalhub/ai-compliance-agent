---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Training Data Extraction
description: An adversary uses carefully crafted prompts to cause a language model to reproduce verbatim segments of its training data, potentially exposing personal data or confidential information.
tags: ["misuse", "training-data-extraction", "privacy", "llm", "adversarial", "nist-ai-100-2", "gdpr"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

NIST AI 100-2 §4.3. GDPR Art. 5(1)(e) (storage limitation) is violated when personal data memorised in model weights is reproduced on demand. EU AI Act Art. 53 training data transparency requirements do not eliminate this risk.

# Instance

```json
{{
  "id": "misuse-training_data_extraction",
  "name": "Training Data Extraction",
  "description": "An adversary uses carefully crafted prompts to cause a language model to reproduce verbatim segments",
  "misuse_kind": "DATA_LEAKAGE",
  "intentionality": "ADVERSARIAL",
  "likelihood": "LIKELY",
  "impact": "HIGH",
  "actor_roles": ["END_USER"],
  "rationale": "NIST AI 100-2 §4.3. GDPR Art. 5(1)(e) (storage limitation) is violated when personal data memorised "
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [NIST AI 100-2](../regulatory-refs/nist-ai-100-2.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
