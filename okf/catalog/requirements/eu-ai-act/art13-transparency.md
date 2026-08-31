---
type: Requirement
title: EU AI Act Art. 13 — Transparency and Provision of Information to Deployers
description: High-risk AI systems must be designed to enable deployers to understand how to operate them correctly and interpret their output, accompanied by instructions for use.
tags: ["eu-ai-act", "high-risk", "transparency", "explainability", "deployer"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-13",
  "name": "EU AI Act Art. 13 — Transparency and Provision of Information to Deployers",
  "description": "Requires transparent AI output interpretation and complete instructions for use for high-risk AI.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 13",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "High-risk AI systems shall be designed and developed in such a way to ensure that their operation is sufficiently transp...",
  "summary": "Requires transparent AI output interpretation and complete instructions for use for high-risk AI.",
  "kind": "TRANSPARENCY",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

High-risk AI systems shall be designed and developed in such a way to ensure that their operation is sufficiently transparent to enable deployers to interpret the system's output and use it appropriately. Providers shall ensure that high-risk AI systems are accompanied by instructions for use in appropriate digital format including information on the intended purpose, level of accuracy and performance, known limitations, and circumstances in which the AI system may lead to errors.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
