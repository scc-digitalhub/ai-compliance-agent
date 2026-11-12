---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: DomainDescriptor
description: Domain and use-case classification for a project or entity.
tags: [foundation, domain, classification]
schema: ../okb/schemas/DomainDescriptor.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`DomainDescriptor` classifies an entity by application domain, enabling
domain-specific compliance rule evaluation. It is embedded in Project, Data, and Model.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | yes | Application domain — e.g. `healthcare`, `finance`, `nlp`. |
| `subdomain` | string | no | Optional narrower classification. |
| `use_case` | string | no | Specific use-case description. |

# Examples

```json
{
  "domain": "healthcare",
  "subdomain": "radiology",
  "use_case": "Automated tumour detection in CT scans"
}
```
