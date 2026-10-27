---
type: Compliance Model Type
title: RetentionPolicy
description: Data retention policy defining scope, legal basis, purposes, validity period, and accountability.
tags: [data, governance, retention, gdpr, legal]
schema: ../okb/schemas/RetentionPolicy.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`RetentionPolicy` specifies which data artefacts are covered, why they are kept
(legal basis), the permitted purposes, and who is accountable. It is embedded in
[DataGovernance](/data/DataGovernance.md). Legal references link to
[RegulatoryRef](/foundations/RegulatoryRef.md) entries.

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `applies_to` | set of enum | no | Data categories covered — `RAW_DATA` · `TRAINING_DATA` · `VALIDATION_DATA` · `TEST_DATA` · `SYNTHETIC_DATA` · `AUGMENTED_DATA` · `TEST_REPORTS` · `DOCUMENTATION` · `OTHER` |
| `retention_basis` | enum | no | `PURPOSE_NECESSITY` \| `LEGAL_OBLIGATION` \| `CONSENT_DEPENDENT` \| `SECURITY_MONITORING` \| `OTHER` |
| `retention_basis_value` | string | no | Free text when `retention_basis` is `OTHER`. |
| `purposes` | set of enum | no | `TRAINING` · `VALIDATION` · `TESTING` · `MONITORING` · `BIAS_DETECTION` · `BIAS_CORRECTION` · `ROBUSTNESS_EVALUATION` · `LEGAL_COMPLIANCE` · `RESEARCH` · `ARCHIVING` · `OTHER` |
| `legal_references` | set of [RegulatoryRef](/foundations/RegulatoryRef.md) | no | Applicable legal bases. |
| `justification` | string | no | Free-text rationale. |
| `owner` | [ActorRef](/foundations/ActorRef.md) | no | Accountable owner. |
| `approver` | [ActorRef](/foundations/ActorRef.md) | no | Sign-off authority. |
| `valid_from` | datetime | no | Policy effective date. |
| `valid_until` | datetime | no | Policy expiry date. |
