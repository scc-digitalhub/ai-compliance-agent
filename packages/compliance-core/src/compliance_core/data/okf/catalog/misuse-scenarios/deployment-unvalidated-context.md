---
type: MisuseScenario
title: Deployment in Unvalidated Context
description: An AI model validated for one domain, population, or geographic context is deployed in a different context without re-validation, producing unreliable or discriminatory outputs.
tags: ["misuse", "distribution-shift", "out-of-scope", "validation", "eu-ai-act"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 9 requires risk management to consider reasonably foreseeable misuse including out-of-scope deployment. Dataset shift and demographic differences between training and deployment populations frequently cause performance degradation.

# Instance

```json
{{
  "id": "misuse-deployment_unvalidated_context",
  "name": "Deployment in Unvalidated Context",
  "description": "An AI model validated for one domain, population, or geographic context is deployed in a different c",
  "misuse_kind": "DEPLOYMENT_IN_UNVALIDATED_CONTEXT",
  "intentionality": "NEGLIGENT",
  "likelihood": "LIKELY",
  "impact": "MEDIUM",
  "actor_roles": ["DEPLOYER"],
  "rationale": "EU AI Act Art. 9 requires risk management to consider reasonably foreseeable misuse including out-of"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
