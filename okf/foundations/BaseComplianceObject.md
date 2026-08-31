---
type: Compliance Model Type
title: BaseComplianceObject
description: Lightweight identity and descriptive base inherited by all compliance model objects.
tags: [foundation, identity, base]
schema: ../okb/schemas/BaseComplianceObject.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`BaseComplianceObject` is the common identity base extended by the major compliance
model types: [AttributeRef](/context/AttributeRef.md), [GroupSpec](/context/GroupSpec.md),
[MisuseScenario](/context/MisuseScenario.md), [Requirement](/context/Requirement.md),
and [Metric](/metrics/Metric.md).

It provides a lightweight identity — a string key and scoping namespace — without
the full versioning or audit metadata carried by first-class platform entities.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Locally unique identifier. |
| `namespace` | string | no | Scoping context (org, project, registry). |
| `name` | string | yes | Human-readable display name. |
| `description` | string | no | Free-text description. |

# Examples

```json
{
  "id": "attr-age-001",
  "namespace": "eu-healthcare-project",
  "name": "Patient Age",
  "description": "Age of the patient at time of model inference."
}
```
