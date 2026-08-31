---
type: Compliance Model Type
title: RegulatoryRef
description: Normative reference to a regulatory framework, article, or section.
tags: [foundation, regulation, legal, reference]
schema: ../okb/schemas/RegulatoryRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`RegulatoryRef` points to the authoritative source of a compliance obligation. It
is embedded in [Requirement](/context/Requirement.md), [RetentionPolicy](/data/RetentionPolicy.md),
and [ComplianceContext](/context/ComplianceContext.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `framework` | string | yes | Framework identifier — e.g. `EU_AI_ACT`, `NIST_AI_RMF`, `ISO_42001`. |
| `article` | string | no | Article or section — e.g. `Art. 9`, `MAP 1.1`. |
| `version` | string | no | Framework version string. |
| `uri` | string (URI) | no | Link to official text. |

# Examples

```json
[
  { "framework": "EU_AI_ACT",    "article": "Art. 9",  "version": "2024/1689" },
  { "framework": "NIST_AI_RMF",  "article": "MAP 1.1" },
  { "framework": "ISO_42001",    "version": "2023" }
]
```
