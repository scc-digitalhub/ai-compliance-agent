---
type: GroupSpec
title: Persons with a Criminal Record
description: Persons who have been convicted of a criminal offence and have served their sentence — data concerning them is subject to GDPR Art. 10 restrictions; at risk of perpetual AI-driven exclusion.
tags: ["group", "protected", "criminal-record", "reintegration", "gdpr-art10"]
schema: ../../okb/schemas/GroupSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

GDPR Art. 10 restricts processing of criminal conviction data to official authority or authorised contexts. AI systems using historical conviction data in employment, housing, or credit decisions risk perpetuating discrimination and undermining social reintegration.

# Instance

```json
{{
  "id": "group-persons_with_criminal_record",
  "name": "Persons with a Criminal Record",
  "description": "Persons who have been convicted of a criminal offence and have served their sentence — data concerni",
  "group_kind": "DEMOGRAPHIC",
  "group_role": "DECISION_SUBJECT",
  "vulnerability": "MINORITY_STATUS",
  "defining_attributes": ["AttributeRef: criminal_record"],
  "rationale": "GDPR Art. 10 restricts processing of criminal conviction data to official authority or authorised co"
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Used in ComplianceContext as

- `affected_groups` or `vulnerable_groups`
