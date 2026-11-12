---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Requirement
title: EU AI Act Art. 53 — GPAI Model Obligations
description: All GPAI model providers must maintain technical documentation, supply downstream providers with information, comply with copyright law, and publish a training data summary.
tags: ["eu-ai-act", "gpai", "documentation", "transparency", "copyright"]
schema: ../../okb/schemas/Requirement.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

# Instance

```json
{{
  "id": "req-euai-art-53",
  "name": "EU AI Act Art. 53 — GPAI Model Obligations",
  "description": "Mandates technical documentation, downstream information supply, copyright compliance, and training data summary for all GPAI providers.",
  "source": {{
    "framework": "EU_AI_ACT",
    "article": "Art. 53",
    "version": "2024/1689",
    "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
  }},
  "requirement_text": "Providers of general-purpose AI (GPAI) models shall draw up and keep up-to-date technical documentation including training and evaluation results; provide downstream providers with adequate information and documentation to comply with their own obligations; put in place a policy to respect copyright and related rights; and publish a sufficiently detailed summary about the content used for training the GPAI model.",
  "summary": "Mandates technical documentation, downstream information supply, copyright compliance, and training data summary for all GPAI providers.",
  "kind": "DOCUMENTATION",
  "applicability_status": "APPLICABLE"
}}
```

# Full Requirement Text

Providers of general-purpose AI (GPAI) models shall draw up and keep up-to-date technical documentation including training and evaluation results; provide downstream providers with adequate information and documentation to comply with their own obligations; put in place a policy to respect copyright and related rights; and publish a sufficiently detailed summary about the content used for training the GPAI model.

# Related Concepts

- [EU AI Act RegulatoryRef](../../regulatory-refs/eu-ai-act.md)
- [RiskClassification](/context/RiskClassification.md) — risk level `HIGH` triggers most of these requirements
- [ComplianceContext](/context/ComplianceContext.md) — attach to the context where this requirement applies
