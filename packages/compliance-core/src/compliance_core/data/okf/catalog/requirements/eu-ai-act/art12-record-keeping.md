---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: EU AI Act Art. 12 — Record-keeping and Automatic Logging
description: High-risk AI systems must automatically log events throughout operation to enable post-hoc auditing, incident investigation, and regulatory review.
tags: ["eu-ai-act", "high-risk", "logging", "monitoring", "audit"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-12",
  "name": "EU AI Act Art. 12 — Record-keeping and Automatic Logging",
  "description": "Mandates automatic event logging to support lifecycle traceability and post-market monitoring.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 12",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "High-risk AI systems shall technically allow for the automatic recording of events (logs) over the duration of the lifetime of the system. Logging capabilities shall ensure a level of traceability of the AI system's functioning throughout its lifecycle appropriate to the intended purpose of the system, in particular for identifying risks and substantial modifications, and facilitating post-market monitoring.",
  "summary": "Mandates automatic event logging to support lifecycle traceability and post-market monitoring.",
  "kind": "MONITORING",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

High-risk AI systems shall technically allow for the automatic recording of events (logs) over the duration of the lifetime of the system. Logging capabilities shall ensure a level of traceability of the AI system's functioning throughout its lifecycle appropriate to the intended purpose of the system, in particular for identifying risks and substantial modifications, and facilitating post-market monitoring.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
