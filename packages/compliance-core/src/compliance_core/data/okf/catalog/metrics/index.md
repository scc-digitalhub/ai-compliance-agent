<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# AI Compliance Metrics Catalog

Concrete [Metric](/metrics/Metric.md) instances for AI compliance evaluation.
Each entry includes the formal metric definition, a JSON instance conforming to
the Metric schema, and a Python code snippet for evaluation.

## Fairness and Bias
* [Fairness Metrics](fairness/) — Demographic parity, equalized odds, disparate impact, Theil index, individual fairness, calibration parity

## Data Quality
* [Data Quality Metrics](data-quality/) — Completeness, accuracy, consistency, representativeness gap, label balance, annotation agreement

## Performance and Quality
* [Performance Metrics](performance/) — Accuracy, precision/recall/F1, AUC-ROC, RMSE/MAE, log-loss, out-of-distribution gap

## Robustness
* [Robustness Metrics](robustness/) — Adversarial accuracy, certified robustness, attack success rate, distribution shift delta

## Explainability and Transparency
* [Explainability Metrics](explainability/) — Mean |SHAP|, local fidelity, faithfulness, feature importance stability, decision coverage

## Calibration
* [Calibration Metrics](calibration/) — Expected Calibration Error (ECE), Maximum Calibration Error (MCE), Brier score

## Privacy
* [Privacy Metrics](privacy/) — Differential privacy ε, k-anonymity, l-diversity, membership inference AUC, memorisation rate

## Environmental
* [Environmental Metrics](environmental/) — CO₂ equivalent, Software Carbon Intensity (SCI), energy per inference
