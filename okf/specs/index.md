# Compliance Specification Containers

High-level typed extension specs that attach compliance metadata to specific
platform entity kinds. Each spec inherits the three core compliance fields from
[ComplianceSpec](ComplianceSpec.md) (`objectives`, `compliance_status`,
`documentation`) and may add entity-kind-specific fields.

* [ComplianceSpec](ComplianceSpec.md) - Base compliance extension inherited by all entity-level specs.
* [ProjectComplianceSpec](ProjectComplianceSpec.md) - Compliance container for a **project** (`kind: ai-compliance`).
* [ModelComplianceSpec](ModelComplianceSpec.md) - Compliance container for a **model** (`kind: model-compliance`).
* [DataComplianceSpec](DataComplianceSpec.md) - Compliance container for a **data item or artifact** (`kind: data-compliance`).
* [ModelServiceComplianceSpec](ModelServiceComplianceSpec.md) - Compliance container for a **model service** (`kind: model-service-compliance`).
* [OperationComplianceSpec](OperationComplianceSpec.md) - Compliance container for an **operation / function** (`kind: operation-compliance`).
* [ReportSpec](ReportSpec.md) - Compliance container for a **report** entity (`kind: compliance-report`).
