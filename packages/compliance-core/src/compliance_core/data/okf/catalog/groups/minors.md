---
type: GroupSpec
title: Minors / Children
description: Persons under 18 years of age — explicitly identified as a vulnerable group in EU AI Act Art. 5 (exploitation of vulnerabilities) and Art. 9(1) of GDPR (children's consent).
tags: ["group", "vulnerable", "minors", "children", "eu-ai-act", "gdpr"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Children are explicitly identified in EU AI Act Art. 5(1)(b) as a group whose vulnerabilities (due to age) must not be exploited by AI systems. GDPR Art. 8 sets 16 as the default age threshold for consent.

# Instance

```json
{{
  "id": "group-minors",
  "name": "Minors / Children",
  "description": "Persons under 18 years of age — explicitly identified as a vulnerable group in EU AI Act Art. 5 (exp",
  "group_kind": "VULNERABLE",
  "group_role": "TARGET_SUBJECT",
  "vulnerability": "AGE",
  "defining_attributes": ["AttributeRef: age"],
  "rationale": "Children are explicitly identified in EU AI Act Art. 5(1)(b) as a group whose vulnerabilities (due t"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` — this group is directly impacted by the AI system's decisions or outputs
- `vulnerable_groups` — this group requires heightened protection measures
