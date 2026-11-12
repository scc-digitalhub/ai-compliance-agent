<!--
SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler

SPDX-License-Identifier: Apache-2.0
-->

# AI Compliance Framework — Bundle Update Log

## 2026-08-28
* **Addition**: Added the **AI Compliance Metrics Catalog** (`catalog/metrics/`) with 40 metric instances across 8 concern areas: fairness (8), data quality (6), performance (6), robustness (4), explainability (5), calibration (3), privacy (5), environmental (3). Each metric includes a JSON instance conforming to the Metric schema and a Python code snippet for evaluation. Updated catalog and root indexes.
* **Extension**: Extended the Compliance Concept Catalog with 58 new concept instances from EU/international/Italian jurisdictions: 10 new RegulatoryRefs (DSA, NIS2, EU Data Act, EU Charter, CoE AI Convention, UNESCO, ISO 23894, ISO TR 24027, NIST AI 100-2, Garante Privacy, EBA/ECB ML); 28 new Requirements across 6 new framework sub-directories; 5 new GroupSpec instances; 7 new AttributeRef instances; 6 new MisuseScenario instances. Updated all catalog indexes.
* **Addition**: Created the **Compliance Concept Catalog** (`catalog/`) with 71 concept instance files across 5 groups: 5 RegulatoryRef instances, 17 Requirement instances (EU AI Act + GDPR), 14 GroupSpec instances, 12 MisuseScenario instances, and 15 AttributeRef instances. Updated root index.
* **Addition**: Added [ReportSpec](specs/ReportSpec.md) to the Compliance Specification Containers group.
* **Move**: Relocated [ComplianceSpec](specs/ComplianceSpec.md) from `compliance/` to `specs/`; updated all cross-links bundle-wide.
* **Addition**: Added the **Compliance Specification Containers** group with five concept documents derived from the `specs/` Java package: [ProjectComplianceSpec](specs/ProjectComplianceSpec.md), [ModelComplianceSpec](specs/ModelComplianceSpec.md), [DataComplianceSpec](specs/DataComplianceSpec.md), [ModelServiceComplianceSpec](specs/ModelServiceComplianceSpec.md), and [OperationComplianceSpec](specs/OperationComplianceSpec.md). Updated [index.md](index.md) with the new group.
* **Initialization**: Created the full OKF v0.2 bundle from the AI Compliance Framework specification and Java implementation classes. Established all concept documents across eight groups: Foundations, Compliance Context, Data Governance, Metrics, Compliance Objectives, Reports, Compliance Status & Documentation, and Model.
