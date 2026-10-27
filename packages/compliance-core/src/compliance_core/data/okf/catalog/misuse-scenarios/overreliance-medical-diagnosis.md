---
type: MisuseScenario
title: Overreliance on AI Medical Diagnosis
description: Clinicians accept AI diagnostic outputs without critical review, leading to missed diagnoses or incorrect treatment in cases where the AI model is operating outside its validated distribution.
tags: ["misuse", "overreliance", "healthcare", "medical-ai", "patient-safety"]
schema: ../../okb/schemas/MisuseScenario.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

Healthcare AI carries life-critical risks. EU AI Act Annex III covers AI safety components in medical devices. Distribution shift between training and deployment populations is a common failure mode in diagnostic AI.

# Instance

```json
{{
  "id": "misuse-overreliance_medical_diagnosis",
  "name": "Overreliance on AI Medical Diagnosis",
  "description": "Clinicians accept AI diagnostic outputs without critical review, leading to missed diagnoses or inco",
  "misuse_kind": "OVERRELIANCE",
  "intentionality": "NEGLIGENT",
  "likelihood": "POSSIBLE",
  "impact": "CRITICAL",
  "actor_roles": ["DEPLOYER", "END_USER"],
  "rationale": "Healthcare AI carries life-critical risks. EU AI Act Annex III covers AI safety components in medica"
}}
```

# Regulatory Basis

- [EU AI Act](../regulatory-refs/eu-ai-act.md)
- [GDPR](../regulatory-refs/gdpr.md)

# Suggested Mitigations

See [MitigationAction](/compliance/MitigationAction.md) for mitigation lifecycle tracking.
