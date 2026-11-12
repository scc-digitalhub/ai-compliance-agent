---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Social Scoring Misuse
description: Using an AI system to evaluate or classify natural persons or groups based on social behaviour or personal characteristics in social contexts, leading to detrimental treatment.
tags: ["misuse", "social-scoring", "prohibited", "eu-ai-act-art5", "discrimination"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 5(1)(c) explicitly prohibits social scoring AI systems. Risk arises when general-purpose scoring or recommendation models are re-purposed to assess personal trustworthiness.

# Instance

```json
{{
  "id": "misuse-social_scoring",
  "name": "Social Scoring Misuse",
  "description": "Using an AI system to evaluate or classify natural persons or groups based on social behaviour or pe",
  "misuse_kind": "OUT_OF_SCOPE_USE",
  "intentionality": "INTENTIONAL",
  "likelihood": "POSSIBLE",
  "impact": "HIGH",
  "actor_roles": ["PROVIDER", "DEPLOYER"],
  "rationale": "EU AI Act Art. 5(1)(c) explicitly prohibits social scoring AI systems. Risk arises when general-purp"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
