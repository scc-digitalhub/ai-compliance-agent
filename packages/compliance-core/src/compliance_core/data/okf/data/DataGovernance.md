---
type: Compliance Model Type
title: DataGovernance
description: Governance metadata bundle for a dataset, covering sensitivity level, license, retention, and consent.
tags: [data, governance, privacy, gdpr, sensitivity]
schema: ../okb/schemas/DataGovernance.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`DataGovernance` is the compliance envelope embedded in every Data entity. It
aggregates the four governance dimensions: sensitivity classification,
SPDX license, [retention policy](/data/RetentionPolicy.md), and
[consent specification](/data/ConsentSpec.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sensitivity` | enum | yes | `NONE` \| `PII` \| `SENSITIVE` \| `RESTRICTED` \| `PROHIBITED` |
| `license` | string | no | SPDX license expression (e.g. `CC-BY-4.0`, `Apache-2.0`). |
| `retention` | [RetentionPolicy](/data/RetentionPolicy.md) | no | How long and why data is kept. |
| `consent` | [ConsentSpec](/data/ConsentSpec.md) | no | Consent requirements and conditions. |
