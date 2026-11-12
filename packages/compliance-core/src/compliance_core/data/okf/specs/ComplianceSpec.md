---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Specification
title: ComplianceSpec
description: Top-level compliance extension attached to any first-class entity (data, model, model service, project), carrying objectives, status, and documentation.
tags: [compliance, spec, extension, objectives, status]
schema: ../okb/schemas/ComplianceSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ComplianceSpec` is the compliance extension point. It is attached as a typed
extension to any platform entity (data item, artifact, model, project). It
collects the [ComplianceObjective](/objectives/ComplianceObjective.md)s that govern
the entity, the current [ComplianceStatus](/compliance/ComplianceStatus.md), and an
optional [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) artifact.

Concrete extension types (`DataComplianceSpec`, `ModelComplianceSpec`, etc.) extend
`ComplianceSpec` without adding extra fields; they differ only in the entity kinds
they are declared applicable to.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objectives` | set of [ComplianceObjective](/objectives/ComplianceObjective.md) | no | Normative constraints governing this entity. |
| `compliance_status` | [ComplianceStatus](/compliance/ComplianceStatus.md) | no | Current compliance verdict. |
| `documentation` | [ComplianceDocumentation](/compliance/ComplianceDocumentation.md) | no | Structured compliance documentation. |
