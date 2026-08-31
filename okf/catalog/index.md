# Compliance Concept Catalog

Concrete instances of the framework's core compliance concepts, derived from the
EU AI Act (Regulation (EU) 2024/1689), GDPR (Regulation (EU) 2016/679),
NIST AI RMF (NIST AI 100-1), ISO/IEC 42001:2023, and Italian AgID guidelines.

An AI agent can use these instances as candidate suggestions when populating a
compliance context for a given domain, use case, and deployment scenario.

## Regulatory References

Pre-defined references to major AI-relevant regulatory frameworks and standards.

* [Regulatory References](regulatory-refs/) — EU AI Act, GDPR, DSA, NIS2, EU Data Act, EU Charter, CoE AI Convention, UNESCO, ISO 42001/23894/TR 24027, NIST AI 100-2, EBA/ECB ML, AgID LLGG, Garante Privacy

## Requirements

Normative requirements extracted from each framework.

* [EU AI Act Requirements](requirements/eu-ai-act/) — Articles 5, 9–15, 17, 50, 53
* [GDPR Requirements](requirements/gdpr/) — Articles 5, 6, 9, 22, 25, 35
* [DSA Requirements](requirements/dsa/) — Articles 27, 34, 35
* [NIS2 Requirements](requirements/nis2/) — Articles 21, 23
* [EU Charter Requirements](requirements/eu-charter/) — Articles 8, 21, 47
* [UNESCO AI Ethics Requirements](requirements/unesco/) — 7 ethical principles
* [ISO/IEC 42001 Annex A](requirements/iso-42001-annex-a/) — Controls A.3.3, A.6.1, A.7.2, A.9.2, A.10.1
* [EBA/ECB ML Guidelines](requirements/eba-ml/) — Model validation, explainability, bias testing

## Population Groups

Standardised group descriptors for affected, vulnerable, and protected populations.

* [Groups](groups/) — 19 groups: vulnerable, protected, operational, system-interaction, language minorities, gig workers, pregnant persons, criminal record holders, and persons with low digital literacy

## Misuse Scenarios

Foreseeable misuse scenarios for AI systems, mapped to EU AI Act, DSA, and NIST AI 100-2.

* [Misuse Scenarios](misuse-scenarios/) — 18 scenarios: societal misuse, operational misuse, adversarial attacks, privacy attacks, platform misuse, domain-specific misuse

## Attributes

Protected and sensitive attribute descriptors for fairness and privacy compliance.

* [Attributes](attributes/) — 22 attributes: GDPR special categories, EU AI Act/Charter protected characteristics, AI-derived scores

## AI Compliance Metrics

Concrete metric instances with JSON definitions and Python evaluation code.

* [Fairness Metrics](metrics/fairness/) — 8 metrics: demographic parity, disparate impact, equalized odds, individual fairness, calibration parity
* [Data Quality Metrics](metrics/data-quality/) — 6 metrics: completeness, accuracy, consistency, representativeness gap, label balance, annotation agreement
* [Performance Metrics](metrics/performance/) — 6 metrics: accuracy, F1, AUC-ROC, RMSE/MAE, log-loss, OOD gap
* [Robustness Metrics](metrics/robustness/) — 4 metrics: adversarial accuracy, certified radius, attack success rate, MMD
* [Explainability Metrics](metrics/explainability/) — 5 metrics: mean |SHAP|, LIME fidelity, faithfulness, stability, decision coverage
* [Calibration Metrics](metrics/calibration/) — 3 metrics: ECE, MCE, Brier score
* [Privacy Metrics](metrics/privacy/) — 5 metrics: DP epsilon, k-anonymity, l-diversity, MI AUC, memorisation rate
* [Environmental Metrics](metrics/environmental/) — 3 metrics: CO₂e, SCI, energy per inference
