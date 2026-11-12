---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: GDPR Art. 6 — Lawful Basis for Processing Personal Data
description: Processing of personal data is only lawful if it rests on one of six legal bases: consent, contract, legal obligation, vital interests, public task, or legitimate interests.
tags: ["gdpr", "consent", "lawful-basis", "data-processing"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-gdpr-art-6",
  "name": "GDPR Art. 6 — Lawful Basis for Processing Personal Data",
  "description": "Requires a documented legal basis for any personal data processing by the AI system.",
  "source": {{
    "framework": "GDPR",
    "article": "Art. 6",
    "version": "2016/679",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
  }},
  "requirement_text": "Processing of personal data shall be lawful only if at least one of the following applies: the data subject has given consent; processing is necessary for the performance of a contract; processing is necessary for compliance with a legal obligation; processing is necessary to protect vital interests; processing is necessary for a task carried out in the public interest or in exercise of official authority; or processing is necessary for the legitimate interests of the controller, except where overridden by the data subject's fundamental rights.",
  "summary": "Requires a documented legal basis for any personal data processing by the AI system.",
  "kind": "DATA_GOVERNANCE",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Processing of personal data shall be lawful only if at least one of the following applies: the data subject has given consent; processing is necessary for the performance of a contract; processing is necessary for compliance with a legal obligation; processing is necessary to protect vital interests; processing is necessary for a task carried out in the public interest or in exercise of official authority; or processing is necessary for the legitimate interests of the controller, except where overridden by the data subject's fundamental rights.

# Related Concepts

- [GDPR RegulatoryRef](../../regulatory-refs/gdpr.md)
- [DataGovernance](/data/DataGovernance.md) — where GDPR data requirements are recorded
- [ConsentSpec](/data/ConsentSpec.md) — for consent-basis requirements
