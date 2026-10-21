---
type: Requirement
title: EU AI Act Art. 5 — Prohibited AI Practices
description: Prohibition on AI systems using subliminal techniques, exploiting vulnerabilities, social scoring, real-time biometric identification, and emotion recognition in workplaces/schools.
tags: ["eu-ai-act", "prohibited", "risk", "biometrics", "manipulation"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-5",
  "name": "EU AI Act Art. 5 — Prohibited AI Practices",
  "description": "Prohibits AI systems that manipulate, exploit, or surveil individuals in ways incompatible with fundamental rights.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 5",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "AI systems that deploy subliminal, manipulative, or deceptive techniques, exploit vulnerabilities of specific groups, perform social scoring, real-time biometric identification in public spaces for law enforcement (outside narrow exceptions), infer emotions in workplaces or educational institutions, or compile facial recognition databases through untargeted scraping are prohibited.",
  "summary": "Prohibits AI systems that manipulate, exploit, or surveil individuals in ways incompatible with fundamental rights.",
  "kind": "DESIGN",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

AI systems that deploy subliminal, manipulative, or deceptive techniques, exploit vulnerabilities of specific groups, perform social scoring, real-time biometric identification in public spaces for law enforcement (outside narrow exceptions), infer emotions in workplaces or educational institutions, or compile facial recognition databases through untargeted scraping are prohibited.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
