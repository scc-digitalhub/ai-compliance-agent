---
type: Compliance Model Type
title: ConsentSpec
description: Specification of data subject consent requirements, legal basis, and GDPR quality flags.
tags: [data, governance, consent, gdpr, privacy]
schema: ../okb/schemas/ConsentSpec.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`ConsentSpec` documents the consent requirements for a dataset and the GDPR
quality attributes of that consent (freely given, specific, informed,
unambiguous, explicit). It is embedded in [DataGovernance](/data/DataGovernance.md).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `consent_required` | boolean | yes | Whether data subject consent is required. |
| `consent_basis` | enum | no | Legal basis for consent — see below. |
| `consent_basis_value` | string | no | Free text when `consent_basis` is `OTHER`. |
| `applies_to` | set of enum | no | Processing activities covered — `COLLECTION` · `STORAGE` · `TRAINING` · `VALIDATION` · `TESTING` · `PROFILING` · `AUTOMATED_DECISION_SUPPORT` · `BIAS_DETECTION` · `BIAS_CORRECTION` · `ROBUSTNESS_EVALUATION` · `DATA_SHARING` · `OTHER` |
| `data_categories` | set of enum | no | `PERSONAL` · `SENSITIVE` · `ANONYMIZED` · `PSEUDONYMIZED` · `SYNTHETIC` · `PUBLICLY_AVAILABLE` · `PROPRIETARY` · `OTHER` |
| `purposes` | set of enum | no | Purposes for which consent is obtained — same values as [RetentionPolicy](/data/RetentionPolicy.md) `purposes`. |
| `freely_given` | boolean | no | Consent was freely given (GDPR Art. 7). |
| `specific` | boolean | no | Consent was specific. |
| `informed` | boolean | no | Data subject was informed. |
| `unambiguous` | boolean | no | Consent was unambiguous. |
| `explicit` | boolean | no | Explicit consent (required for special categories). |

## Consent Basis Values

`GDPR_ARTICLE_6_1_A` · `GDPR_ARTICLE_9_2_A` · `AI_ACT_REAL_WORLD_TESTING` · `OTHER`
