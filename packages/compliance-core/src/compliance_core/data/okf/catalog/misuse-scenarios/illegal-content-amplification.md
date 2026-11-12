---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Illegal Content Amplification via AI Moderation Failure
description: Failures or adversarial evasion of AI-based content moderation systems allow illegal content (CSAM, terrorist content, illegal hate speech) to be amplified or escape detection.
tags: ["misuse", "content-moderation", "illegal-content", "dsa", "evasion", "monitoring"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

DSA Art. 34 and 35 require VLOPs to assess and mitigate risks from AI content moderation failures. Content moderation AI can be gamed through adversarial text reformulation, steganographic embedding, or cross-language evasion.

# Instance

```json
{{
  "id": "misuse-illegal_content_amplification",
  "name": "Illegal Content Amplification via AI Moderation Failure",
  "description": "Failures or adversarial evasion of AI-based content moderation systems allow illegal content (CSAM, ",
  "misuse_kind": "MONITORING_EVASION",
  "intentionality": "ADVERSARIAL",
  "likelihood": "POSSIBLE",
  "impact": "CRITICAL",
  "actor_roles": ["END_USER"],
  "rationale": "DSA Art. 34 and 35 require VLOPs to assess and mitigate risks from AI content moderation failures. C"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [NIST AI 100-2](../regulatory-refs/nist-ai-100-2.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
