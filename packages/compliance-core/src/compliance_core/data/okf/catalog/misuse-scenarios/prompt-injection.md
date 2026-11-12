---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: MisuseScenario
title: Prompt Injection Attack
description: Malicious content in user inputs or external data sources overrides the intended instructions of a generative AI system, causing it to produce harmful, deceptive, or policy-violating outputs.
tags: ["misuse", "prompt-injection", "adversarial", "llm", "owasp-llm01", "cybersecurity"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

OWASP LLM Top 10 LLM01. EU AI Act Art. 15 requires high-risk AI to be resilient against manipulation by third parties. Prompt injection is the primary attack vector for instruction-following LLMs and agentic AI systems.

# Instance

```json
{{
  "id": "misuse-prompt_injection",
  "name": "Prompt Injection Attack",
  "description": "Malicious content in user inputs or external data sources overrides the intended instructions of a g",
  "misuse_kind": "PROMPT_INJECTION",
  "intentionality": "ADVERSARIAL",
  "likelihood": "LIKELY",
  "impact": "HIGH",
  "actor_roles": ["END_USER"],
  "rationale": "OWASP LLM Top 10 LLM01. EU AI Act Art. 15 requires high-risk AI to be resilient against manipulation"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
