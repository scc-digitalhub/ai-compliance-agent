---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: EU AI Act Art. 50 — Transparency for Limited-Risk AI Systems
description: Providers of AI systems interacting with natural persons (chatbots) and of AI-generated content (deepfakes) must ensure users are informed they are interacting with AI or viewing synthetic content.
tags: ["eu-ai-act", "limited-risk", "transparency", "chatbot", "deepfake", "disclosure"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-50",
  "name": "EU AI Act Art. 50 — Transparency for Limited-Risk AI Systems",
  "description": "Requires disclosure when users interact with chatbots or encounter AI-generated synthetic content.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 50",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "Providers of AI systems intended to interact directly with natural persons shall ensure that those persons are informed that they are interacting with an AI system, in a clear and distinguishable manner, at the latest at the start of interaction, except where this is evident. Providers of AI systems generating synthetic audio, image, video, or text content shall ensure the outputs are marked as AI-generated using machine-readable formats.",
  "summary": "Requires disclosure when users interact with chatbots or encounter AI-generated synthetic content.",
  "kind": "TRANSPARENCY",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Providers of AI systems intended to interact directly with natural persons shall ensure that those persons are informed that they are interacting with an AI system, in a clear and distinguishable manner, at the latest at the start of interaction, except where this is evident. Providers of AI systems generating synthetic audio, image, video, or text content shall ensure the outputs are marked as AI-generated using machine-readable formats.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
