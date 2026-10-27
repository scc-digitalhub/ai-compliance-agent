---
type: MisuseScenario
title: Automation Bias in High-stakes Decisions
description: Human operators defer uncritically to AI recommendations in high-stakes contexts (medical, judicial, credit) without applying independent judgment, effectively bypassing the human oversight requirement.
tags: ["misuse", "automation-bias", "high-risk", "eu-ai-act-art14", "human-oversight"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 14 requires high-risk AI to be designed to counteract automation bias. Studies in radiology, credit underwriting, and criminal sentencing show widespread over-reliance on algorithmic outputs.

# Instance

```json
{{
  "id": "misuse-automation_bias_high_stakes",
  "name": "Automation Bias in High-stakes Decisions",
  "description": "Human operators defer uncritically to AI recommendations in high-stakes contexts (medical, judicial,",
  "misuse_kind": "AUTOMATION_BIAS",
  "intentionality": "NEGLIGENT",
  "likelihood": "LIKELY",
  "impact": "HIGH",
  "actor_roles": ["DEPLOYER", "END_USER"],
  "rationale": "EU AI Act Art. 14 requires high-risk AI to be designed to counteract automation bias. Studies in rad"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
