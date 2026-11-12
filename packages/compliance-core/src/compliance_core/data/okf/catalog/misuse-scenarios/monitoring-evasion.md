---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Monitoring Evasion
description: An adversary or misbehaving user detects and avoids the conditions under which an AI system is monitored, causing the monitoring system to fail to detect policy violations or performance degradation.
tags: ["misuse", "monitoring-evasion", "adversarial", "drift", "audit"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 12 mandates logging, and Art. 15 requires robustness measures. Adversaries aware of monitoring thresholds can craft inputs that remain below detection limits while still causing harm.

# Instance

```json
{{
  "id": "misuse-monitoring_evasion",
  "name": "Monitoring Evasion",
  "description": "An adversary or misbehaving user detects and avoids the conditions under which an AI system is monit",
  "misuse_kind": "MONITORING_EVASION",
  "intentionality": "ADVERSARIAL",
  "likelihood": "UNLIKELY",
  "impact": "MEDIUM",
  "actor_roles": ["END_USER"],
  "rationale": "EU AI Act Art. 12 mandates logging, and Art. 15 requires robustness measures. Adversaries aware of m"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
