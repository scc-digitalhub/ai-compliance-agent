---
type: Requirement
title: EU AI Act Art. 14 — Human Oversight
description: High-risk AI systems must be designed to allow effective human oversight to prevent or minimise risks, with measures enabling humans to monitor, intervene, halt, or override outputs.
tags: ["eu-ai-act", "high-risk", "human-oversight", "intervention", "safety"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-14",
  "name": "EU AI Act Art. 14 — Human Oversight",
  "description": "Mandates design that enables natural persons to monitor, understand, and override high-risk AI decisions.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 14",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "High-risk AI systems shall be designed and developed in such a way, including with appropriate human-machine interface t...",
  "summary": "Mandates design that enables natural persons to monitor, understand, and override high-risk AI decisions.",
  "kind": "HUMAN_OVERSIGHT",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

High-risk AI systems shall be designed and developed in such a way, including with appropriate human-machine interface tools, that they can be effectively overseen by natural persons during the period in which the AI system is in use. Natural persons shall be able to understand the capacities and limitations of the high-risk AI system, be aware of automation bias, correctly interpret its output, decide not to use it, intervene on or interrupt its operation, and where applicable, decide not to make use of the decision issued.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
