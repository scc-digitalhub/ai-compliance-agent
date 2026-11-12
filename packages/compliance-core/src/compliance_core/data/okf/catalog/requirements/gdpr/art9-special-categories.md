---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: GDPR Art. 9 — Processing of Special Categories of Personal Data
description: Processing of racial/ethnic origin, political opinions, religious beliefs, trade union membership, genetic/biometric data, health data, sex life, or sexual orientation data is prohibited unless an explicit exemption applies.
tags: ["gdpr", "special-categories", "sensitive-data", "biometrics", "health", "privacy"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-gdpr-art-9",
  "name": "GDPR Art. 9 — Processing of Special Categories of Personal Data",
  "description": "Prohibits processing special-category sensitive data without an explicit GDPR Art. 9(2) exemption.",
  "source": {{
    "framework": "GDPR",
    "article": "Art. 9",
    "version": "2016/679",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
  }},
  "requirement_text": "Processing of personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, biometric data for the purpose of uniquely identifying a natural person, data concerning health or data concerning a natural person's sex life or sexual orientation shall be prohibited, unless one of the specific exemptions in Art. 9(2) applies (e.g. explicit consent, vital interests, substantial public interest, medical purposes).",
  "summary": "Prohibits processing special-category sensitive data without an explicit GDPR Art. 9(2) exemption.",
  "kind": "DATA_PROTECTION",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Processing of personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, biometric data for the purpose of uniquely identifying a natural person, data concerning health or data concerning a natural person's sex life or sexual orientation shall be prohibited, unless one of the specific exemptions in Art. 9(2) applies (e.g. explicit consent, vital interests, substantial public interest, medical purposes).

# Related Concepts

- [GDPR RegulatoryRef](../../regulatory-refs/gdpr.md)
- [DataGovernance](/data/DataGovernance.md) — where GDPR data requirements are recorded
- [ConsentSpec](/data/ConsentSpec.md) — for consent-basis requirements
