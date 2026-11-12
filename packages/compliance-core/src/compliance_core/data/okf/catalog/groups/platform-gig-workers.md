---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: GroupSpec
title: Platform / Gig Economy Workers
description: Persons engaged through digital labour platforms as independent contractors — subject to algorithmic management and covered by the EU Platform Work Directive (2024).
tags: ["group", "occupational", "gig-economy", "platform-work", "eu-directive", "algorithmic-management"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The EU Platform Work Directive (2024) requires platforms to be transparent about the automated monitoring and decision-making systems that affect gig workers, and mandates human review of significant decisions (e.g. deactivation).

# Instance

```json
{{
  "id": "group-platform_gig_workers",
  "name": "Platform / Gig Economy Workers",
  "description": "Persons engaged through digital labour platforms as independent contractors — subject to algorithmic",
  "group_kind": "OCCUPATIONAL",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "EMPLOYMENT_DEPENDENCY",
  "defining_attributes": ["AttributeRef: employment_status"],
  "rationale": "The EU Platform Work Directive (2024) requires platforms to be transparent about the automated monit"
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` or `vulnerable_groups`
