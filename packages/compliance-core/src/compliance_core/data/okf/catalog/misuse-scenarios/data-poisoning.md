---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Training Data Poisoning
description: An adversary injects malicious samples into the training dataset, causing the trained model to produce systematically biased, incorrect, or backdoored outputs for specific inputs.
tags: ["misuse", "data-poisoning", "adversarial", "training", "supply-chain"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 10 requires data governance measures to ensure training data quality and freedom from errors. Data poisoning via supply chain contamination (open datasets, third-party data providers) is increasingly documented.

# Instance

```json
{{
  "id": "misuse-data_poisoning",
  "name": "Training Data Poisoning",
  "description": "An adversary injects malicious samples into the training dataset, causing the trained model to produ",
  "misuse_kind": "DATA_POISONING",
  "intentionality": "ADVERSARIAL",
  "likelihood": "UNLIKELY",
  "impact": "CRITICAL",
  "actor_roles": ["DATA_PROVIDER"],
  "rationale": "EU AI Act Art. 10 requires data governance measures to ensure training data quality and freedom from"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
