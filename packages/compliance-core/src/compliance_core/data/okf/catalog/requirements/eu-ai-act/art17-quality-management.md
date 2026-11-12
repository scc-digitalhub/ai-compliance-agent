---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: EU AI Act Art. 17 — Quality Management System
description: Providers must establish a quality management system ensuring compliance with the AI Act, covering design, development, deployment, monitoring, and post-market processes.
tags: ["eu-ai-act", "high-risk", "quality-management", "governance", "process"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-17",
  "name": "EU AI Act Art. 17 — Quality Management System",
  "description": "Mandates a documented quality management system covering the full AI lifecycle.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 17",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "Providers of high-risk AI systems shall put a quality management system in place that ensures compliance with this Regulation. The system shall cover all phases of the AI lifecycle, including strategy and accountability, design and development controls, data governance procedures, post-market monitoring, incident reporting, and documentation retention.",
  "summary": "Mandates a documented quality management system covering the full AI lifecycle.",
  "kind": "QUALITY_MANAGEMENT",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Providers of high-risk AI systems shall put a quality management system in place that ensures compliance with this Regulation. The system shall cover all phases of the AI lifecycle, including strategy and accountability, design and development controls, data governance procedures, post-market monitoring, incident reporting, and documentation retention.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
