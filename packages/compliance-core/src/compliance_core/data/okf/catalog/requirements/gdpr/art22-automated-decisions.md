---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: GDPR Art. 22 — Automated Individual Decision-making Including Profiling
description: Data subjects have the right not to be subject to solely automated decisions producing legal or similarly significant effects, unless an exemption applies, in which case safeguards including human review must be provided.
tags: ["gdpr", "automated-decisions", "profiling", "human-review", "right-to-explanation"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-gdpr-art-22",
  "name": "GDPR Art. 22 — Automated Individual Decision-making Including Profiling",
  "description": "Entitles data subjects to human review of solely automated decisions with significant effects; mandates explanation and contestation rights.",
  "source": {{
    "framework": "GDPR",
    "article": "Art. 22",
    "version": "2016/679",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
  }},
  "requirement_text": "The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning or similarly significantly affects the data subject. Exemptions exist for contract necessity, legal authorisation, or explicit consent, but in those cases the controller must implement suitable measures to safeguard the data subject's rights including the right to obtain human intervention, to express their point of view, and to contest the decision.",
  "summary": "Entitles data subjects to human review of solely automated decisions with significant effects; mandates explanation and contestation rights.",
  "kind": "HUMAN_OVERSIGHT",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning or similarly significantly affects the data subject. Exemptions exist for contract necessity, legal authorisation, or explicit consent, but in those cases the controller must implement suitable measures to safeguard the data subject's rights including the right to obtain human intervention, to express their point of view, and to contest the decision.

# Related Concepts

- [GDPR RegulatoryRef](../../regulatory-refs/gdpr.md)
- [DataGovernance](/data/DataGovernance.md) — where GDPR data requirements are recorded
- [ConsentSpec](/data/ConsentSpec.md) — for consent-basis requirements
