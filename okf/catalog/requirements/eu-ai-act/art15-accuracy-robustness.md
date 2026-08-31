---
type: Requirement
title: EU AI Act Art. 15 — Accuracy, Robustness, and Cybersecurity
description: High-risk AI systems must achieve appropriate levels of accuracy and be resilient to errors, faults, inconsistencies, and adversarial inputs throughout their lifecycle.
tags: ["eu-ai-act", "high-risk", "accuracy", "robustness", "cybersecurity", "adversarial"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-15",
  "name": "EU AI Act Art. 15 — Accuracy, Robustness, and Cybersecurity",
  "description": "Requires quantified accuracy benchmarks, adversarial robustness, and cybersecurity measures for high-risk AI.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 15",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "High-risk AI systems shall be designed and developed in such a way that they achieve, in the light of their intended pur...",
  "summary": "Requires quantified accuracy benchmarks, adversarial robustness, and cybersecurity measures for high-risk AI.",
  "kind": "QUALITY_MANAGEMENT",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

High-risk AI systems shall be designed and developed in such a way that they achieve, in the light of their intended purpose, an appropriate level of accuracy, robustness, and cybersecurity, and perform consistently in those respects throughout their lifecycle. Resilience measures shall address the performance against manipulation by third parties, technical measures for addressing model vulnerabilities, and back-up and fail-safe plans.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
