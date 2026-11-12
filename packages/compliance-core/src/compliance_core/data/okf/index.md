---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

okf_version: "0.2"
---

# AI Compliance Framework — Knowledge Bundle

This bundle provides the Open Knowledge Format (OKF v0.2) representation of the
**AI Compliance Framework** reference model. Every concept is derived from the
formal specification and its Java implementation classes.

## Foundations

Core identity and utility types reused across the whole framework.

* [BaseComplianceObject](foundations/BaseComplianceObject.md) - Lightweight identity base inherited by all compliance model objects.
* [ActorRef](foundations/ActorRef.md) - Reference to a human user, service account, or automated agent.
* [EntityRef](foundations/EntityRef.md) - Opaque cross-entity reference key.
* [Lineage](foundations/Lineage.md) - DAG of derivation relationships for an artifact.
* [DomainDescriptor](foundations/DomainDescriptor.md) - Domain and use-case classification.
* [RegulatoryRef](foundations/RegulatoryRef.md) - Normative reference to a regulatory framework article or section.

## Compliance Context

Types that describe *how* and *where* an AI project is deployed, including its
risk profile, oversight setup, and applicable regulations.

* [ComplianceContext](context/ComplianceContext.md) - Deployment context anchoring regulations, risk, and oversight.
* [Requirement](context/Requirement.md) - A normative compliance requirement derived from a regulatory framework.
* [AttributeRef](context/AttributeRef.md) - Descriptor of a data attribute with semantic and observability metadata.
* [GroupSpec](context/GroupSpec.md) - Specification of a population group relevant to a compliance context.
* [RiskClassification](context/RiskClassification.md) - Risk classification of an AI system within a compliance context.
* [MisuseScenario](context/MisuseScenario.md) - A foreseeable misuse scenario for an AI system.
* [HumanOversightProfile](context/HumanOversightProfile.md) - Human oversight configuration for an AI deployment.

## Data Governance

Types governing the sensitivity, licensing, retention, and consent aspects of datasets.

* [DataGovernance](data/DataGovernance.md) - Governance metadata bundle for a dataset.
* [RetentionPolicy](data/RetentionPolicy.md) - Data retention policy (duration, basis, purposes).
* [ConsentSpec](data/ConsentSpec.md) - Data subject consent requirements and conditions.
* [FieldSpec](data/FieldSpec.md) - Schema field descriptor for tabular data and model I/O.

## Metrics

Types for defining, composing, and recording measurements.

* [Metric](metrics/Metric.md) - Quantitative or qualitative measure of a defined notion.
* [MetricComposition](metrics/MetricComposition.md) - Aggregation specification for a composite metric.
* [MetricResult](metrics/MetricResult.md) - Observed value of a single metric within a report.
* [ConfidenceInterval](metrics/ConfidenceInterval.md) - Statistical confidence interval for a metric result.
* [UnitOfMeasure](metrics/UnitOfMeasure.md) - Physical unit of measurement for a metric value.
* [ValueRange](metrics/ValueRange.md) - Valid value domain for a metric.

## Compliance Objectives

Types expressing what a compliant entity must satisfy.

* [ComplianceObjective](objectives/ComplianceObjective.md) - Normative constraint binding a Metric to a target value or region.
* [ObjectiveCondition](objectives/ObjectiveCondition.md) - Condition envelope (threshold, range, categorical, statistical, composite).

## Reports

Types for recording evidence produced by validation operations.

* [ReportContent](reports/ReportContent.md) - Content envelope for a compliance report (evaluation, test, or log).

## Compliance Status & Documentation

Types tracking the compliance verdict, findings, mitigations, and documentation
for any first-class entity.

* [ComplianceStatus](compliance/ComplianceStatus.md) - Assessed compliance status at a point in time.
* [ComplianceFinding](compliance/ComplianceFinding.md) - A non-conformance finding from a compliance assessment.
* [MitigationAction](compliance/MitigationAction.md) - Action engaged to resolve a compliance objective violation.
* [ComplianceDocumentation](compliance/ComplianceDocumentation.md) - Structured documentation for an entity's compliance dimension.
* [DocumentSection](compliance/DocumentSection.md) - A titled section within a documentation artifact.

## Model

Types specific to AI/ML model artifacts and their inference interface.

* [InferenceSignature](model/InferenceSignature.md) - Input/output signature of a model's inference function.

## Compliance Specification Containers

High-level typed extension specs that attach compliance metadata to specific
platform entity kinds. Each spec inherits objectives, status, and documentation
from [ComplianceSpec](specs/ComplianceSpec.md) and may add entity-kind-specific fields.

* [ComplianceSpec](specs/ComplianceSpec.md) - Base compliance extension inherited by all entity-level specs.
* [ProjectComplianceSpec](specs/ProjectComplianceSpec.md) - Compliance container for a **project** (`kind: ai-compliance`).
* [ModelComplianceSpec](specs/ModelComplianceSpec.md) - Compliance container for a **model** (`kind: model-compliance`).
* [DataComplianceSpec](specs/DataComplianceSpec.md) - Compliance container for a **data item or artifact** (`kind: data-compliance`).
* [ModelServiceComplianceSpec](specs/ModelServiceComplianceSpec.md) - Compliance container for a **model service** (`kind: model-service-compliance`).
* [OperationComplianceSpec](specs/OperationComplianceSpec.md) - Compliance container for an **operation / function** (`kind: operation-compliance`).
* [ReportSpec](specs/ReportSpec.md) - Compliance container for a **report** entity (`kind: compliance-report`).

## Compliance Concept Catalog

Concrete instances of framework concepts derived from EU AI Act, GDPR, NIST AI RMF,
ISO 42001, and AgID guidelines. Use as candidate suggestions when populating a
compliance context for a domain, use case, and deployment scenario.

* [Regulatory References](catalog/regulatory-refs/) — EU AI Act, GDPR, DSA, NIS2, EU Data Act, EU Charter, CoE AI Convention, UNESCO, ISO 42001/23894/TR 24027, NIST AI 100-2, EBA/ECB ML, AgID LLGG, Garante Privacy
* [Requirements](catalog/requirements/) — EU AI Act · GDPR · DSA · NIS2 · EU Charter · UNESCO · ISO 42001 Annex A · EBA/ECB ML
* [Population Groups](catalog/groups/) — 19 groups across vulnerable, protected, operational, and system-interaction categories
* [Misuse Scenarios](catalog/misuse-scenarios/) — 18 scenarios: societal, operational, adversarial, privacy, platform, and domain-specific
* [Attributes](catalog/attributes/) — 22 attributes: GDPR special categories, EU AI Act/Charter protected characteristics, AI-derived scores

## AI Compliance Metrics

Concrete metric instances with JSON definitions (conforming to the Metric schema)
and Python evaluation code snippets. Covers 40 metrics across 8 concern areas.

* [Metrics Catalog](catalog/metrics/) — Fairness (8) · Data Quality (6) · Performance (6) · Robustness (4) · Explainability (5) · Calibration (3) · Privacy (5) · Environmental (3)
