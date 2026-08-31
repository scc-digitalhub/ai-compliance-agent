---
type: Compliance Specification Container
title: ModelServiceComplianceSpec
description: Compliance extension for a model service entity, inheriting all ComplianceSpec fields with no additional service-specific properties.
tags: [spec, model-service, compliance, inference, deployment]
schema: ../../okb/schemas/ComplianceSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ModelServiceComplianceSpec` is the compliance extension for a **model service**
entity (`kind: model-service-compliance`, `appliesTo: ["service"]`). It extends
[ComplianceSpec](ComplianceSpec.md) without adding service-specific fields;
the inherited spec fields are sufficient.

Compliance objectives attached to a model service typically address runtime
concerns:
- **Input/output tracing** — log completeness and retention
- **Drift detection** — data or concept drift thresholds
- **Resource monitoring** — latency, throughput, and error-rate bounds
- **Guardrails** — prohibited output categories and fallback behaviour

A service compliance spec works in tandem with the
[OperationComplianceSpec](/specs/OperationComplianceSpec.md) of its associated
monitoring and guardrail functions.

# Schema

## Inherited from [ComplianceSpec](ComplianceSpec.md)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objectives` | set of [ComplianceObjective](/objectives/ComplianceObjective.md) | no | Normative constraints governing this service. |
| `compliance_status` | [ComplianceStatus](/compliance/ComplianceStatus.md) | no | Current compliance verdict. |
| `documentation` | [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) | no | System card documentation. |

*No additional fields beyond the inherited ones.*
