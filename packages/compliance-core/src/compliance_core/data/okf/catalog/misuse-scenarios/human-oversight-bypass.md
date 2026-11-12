---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Human Oversight Bypass
description: Workflow or process changes cause a high-risk AI system to be used for final decisions without the human review step that was required for compliance, effectively nullifying the human oversight control.
tags: ["misuse", "human-oversight-bypass", "eu-ai-act-art14", "process"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 14(4) requires deployers to assign human oversight to competent persons and not override safeguards. Under time pressure, operators may route around review steps, creating de facto fully automated decisions.

# Instance

```json
{{
  "id": "misuse-human_oversight_bypass",
  "name": "Human Oversight Bypass",
  "description": "Workflow or process changes cause a high-risk AI system to be used for final decisions without the h",
  "misuse_kind": "HUMAN_OVERSIGHT_BYPASS",
  "intentionality": "NEGLIGENT",
  "likelihood": "POSSIBLE",
  "impact": "HIGH",
  "actor_roles": ["DEPLOYER"],
  "rationale": "EU AI Act Art. 14(4) requires deployers to assign human oversight to competent persons and not overr"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
