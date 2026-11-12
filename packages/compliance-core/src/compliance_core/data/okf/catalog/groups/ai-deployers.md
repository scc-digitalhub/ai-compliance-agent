---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: AI System Deployers
description: Organisations or natural persons that deploy an AI system in a professional context — have specific obligations under EU AI Act Art. 26 and serve as overseers under Art. 14.
tags: ["group", "deployer", "operator", "eu-ai-act"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

EU AI Act Art. 26 defines deployers (formerly 'users') as organisations using high-risk AI in their professional activities. They bear compliance obligations including human oversight implementation and incident reporting.

# Instance

```json
{{
  "id": "group-ai_deployers",
  "name": "AI System Deployers",
  "description": "Organisations or natural persons that deploy an AI system in a professional context — have specific ",
  "group_kind": "OCCUPATIONAL",
  "group_role": "OPERATOR",
  "vulnerability": null,
  "defining_attributes": [],
  "rationale": "EU AI Act Art. 26 defines deployers (formerly 'users') as organisations using high-risk AI in their "
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
