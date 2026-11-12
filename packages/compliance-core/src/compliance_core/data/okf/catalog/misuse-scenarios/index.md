<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# Misuse Scenarios

Concrete [MisuseScenario](/context/MisuseScenario.md) instances for AI systems.
Drawn from EU AI Act prohibited uses (Art. 5), OWASP LLM Top 10, and known
AI failure modes. Use these as candidates in `foreseeable_misuse` within a
[ComplianceContext](/context/ComplianceContext.md).

## Societal Misuse (EU AI Act Art. 5)
* [Social Scoring](social-scoring.md)
* [Subliminal Manipulation](subliminal-manipulation.md)
* [Biometric Categorisation Beyond Scope](biometric-categorisation-beyond-scope.md)

## Operational Misuse
* [Automation Bias in High-stakes Decisions](automation-bias-high-stakes.md)
* [Overreliance on AI Medical Diagnosis](overreliance-medical-diagnosis.md)
* [Human Oversight Bypass](human-oversight-bypass.md)
* [Deployment in Unvalidated Context](deployment-unvalidated-context.md)

## Adversarial Attacks
* [Prompt Injection](prompt-injection.md)
* [Model Extraction](model-extraction.md)
* [Data Poisoning](data-poisoning.md)
* [Adversarial Input](adversarial-input.md)
* [Monitoring Evasion](monitoring-evasion.md)

## Privacy Attacks (NIST AI 100-2)
* [Membership Inference](membership-inference.md)
* [Training Data Extraction](training-data-extraction.md)
* [Model Inversion](model-inversion.md)

## Platform and Systemic Misuse (DSA)
* [Recommender System Manipulation](recommender-manipulation.md)
* [Illegal Content Amplification](illegal-content-amplification.md)

## Domain-specific Misuse
* [Proxy Discrimination in Credit Scoring](proxy-discrimination-credit.md)
