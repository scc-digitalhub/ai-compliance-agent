---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: GDPR Art. 35 — Data Protection Impact Assessment (DPIA)
description: Processing that is likely to result in high risk to natural persons — especially systematic profiling, processing special categories at scale, or systematic monitoring of public areas — requires a prior DPIA.
tags: ["gdpr", "dpia", "impact-assessment", "risk", "profiling"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-gdpr-art-35",
  "name": "GDPR Art. 35 — Data Protection Impact Assessment (DPIA)",
  "description": "Requires a DPIA before deploying AI systems that systematically profile individuals, process sensitive data at scale, or monitor public spaces.",
  "source": {{
    "framework": "GDPR",
    "article": "Art. 35",
    "version": "2016/679",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
  }},
  "requirement_text": "Where a type of processing is likely to result in a high risk to the rights and freedoms of natural persons, the controller shall, prior to the processing, carry out an assessment of the impact of the envisaged processing operations on the protection of personal data. A single assessment may address a set of similar processing operations. The assessment is mandatory for systematic and extensive evaluation of personal aspects through automated processing including profiling; for processing special categories of personal data at large scale; and for systematic monitoring of publicly accessible areas on a large scale.",
  "summary": "Requires a DPIA before deploying AI systems that systematically profile individuals, process sensitive data at scale, or monitor public spaces.",
  "kind": "RISK_MANAGEMENT",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Where a type of processing is likely to result in a high risk to the rights and freedoms of natural persons, the controller shall, prior to the processing, carry out an assessment of the impact of the envisaged processing operations on the protection of personal data. A single assessment may address a set of similar processing operations. The assessment is mandatory for systematic and extensive evaluation of personal aspects through automated processing including profiling; for processing special categories of personal data at large scale; and for systematic monitoring of publicly accessible areas on a large scale.

# Related Concepts

- [GDPR RegulatoryRef](../../regulatory-refs/gdpr.md)
- [DataGovernance](/data/DataGovernance.md) — where GDPR data requirements are recorded
- [ConsentSpec](/data/ConsentSpec.md) — for consent-basis requirements
