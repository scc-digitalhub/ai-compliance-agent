---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Biometric Categorisation Beyond Permitted Scope
description: Using a biometric AI system to infer race, political opinions, trade union membership, religious beliefs, sex life, or sexual orientation beyond the narrow permitted exceptions.
tags: ["misuse", "biometrics", "prohibited", "eu-ai-act-art5", "sensitive-inference"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 5(1)(d) prohibits biometric categorisation systems that infer sensitive attributes. Models trained for one purpose (identity verification) may incidentally learn sensitive proxies.

# Instance

```json
{{
  "id": "misuse-biometric_categorisation_beyond_scope",
  "name": "Biometric Categorisation Beyond Permitted Scope",
  "description": "Using a biometric AI system to infer race, political opinions, trade union membership, religious bel",
  "misuse_kind": "OUT_OF_SCOPE_USE",
  "intentionality": "ACCIDENTAL",
  "likelihood": "POSSIBLE",
  "impact": "CRITICAL",
  "actor_roles": ["PROVIDER", "DEPLOYER"],
  "rationale": "EU AI Act Art. 5(1)(d) prohibits biometric categorisation systems that infer sensitive attributes. M"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
