---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Proxy Discrimination in Credit Scoring
description: A credit scoring model uses features (postcode, shopping patterns, device type) that are highly correlated with protected characteristics, producing discriminatory credit decisions without explicitly using the protected attribute.
tags: ["misuse", "proxy-discrimination", "credit-scoring", "indirect-discrimination", "eba", "fairness"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Annex III and EBA ML guidelines require bias testing. Proxy discrimination occurs when model features encode protected characteristics; this is a documented failure mode in credit AI systems even when protected attributes are explicitly excluded.

# Instance

```json
{{
  "id": "misuse-proxy_discrimination_credit",
  "name": "Proxy Discrimination in Credit Scoring",
  "description": "A credit scoring model uses features (postcode, shopping patterns, device type) that are highly corr",
  "misuse_kind": "OUT_OF_SCOPE_USE",
  "intentionality": "ACCIDENTAL",
  "likelihood": "LIKELY",
  "impact": "HIGH",
  "actor_roles": ["PROVIDER", "DEPLOYER"],
  "rationale": "EU AI Act Annex III and EBA ML guidelines require bias testing. Proxy discrimination occurs when mod"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [NIST AI 100-2](../regulatory-refs/nist-ai-100-2.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
