---
type: Requirement
title: GDPR Art. 25 — Data Protection by Design and by Default
description: Controllers must implement data-minimising technical and organisational measures at the design stage and ensure that, by default, only personal data necessary for each specific purpose is processed.
tags: ["gdpr", "privacy-by-design", "data-minimisation", "default-settings"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-gdpr-art-25",
  "name": "GDPR Art. 25 — Data Protection by Design and by Default",
  "description": "Mandates privacy by design architecture and data-minimising default configurations for AI systems processing personal data.",
  "source": {{
    "framework": "GDPR",
    "article": "Art. 25",
    "version": "2016/679",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
  }},
  "requirement_text": "Taking into account the state of the art, cost of implementation, and the nature, scope, context and purposes of process...",
  "summary": "Mandates privacy by design architecture and data-minimising default configurations for AI systems processing personal data.",
  "kind": "DESIGN",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Taking into account the state of the art, cost of implementation, and the nature, scope, context and purposes of processing, the controller shall implement appropriate technical and organisational measures to implement data-protection principles effectively and integrate the necessary safeguards into the processing in order to meet the requirements of this Regulation. By default, only personal data which are necessary for each specific purpose of the processing are processed.

# Related Concepts

- [GDPR RegulatoryRef](../../regulatory-refs/gdpr.md)
- [DataGovernance](/data/DataGovernance.md) — where GDPR data requirements are recorded
- [ConsentSpec](/data/ConsentSpec.md) — for consent-basis requirements
