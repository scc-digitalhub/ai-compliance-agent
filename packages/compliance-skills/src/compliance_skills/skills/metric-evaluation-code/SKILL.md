---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

name: metric-evaluation-code
description: Generate or validate catalog-grounded Python metric evaluators without executing them.
allowed-tools: get_metric_computation get_evaluation_schema get_session_evaluation_codes generate_metric_evaluation_code validate_metric_evaluation_code record_metric_evaluation_code
metadata:
  compliance-tools: get_metric_computation, get_evaluation_schema, get_session_evaluation_codes, generate_metric_evaluation_code, validate_metric_evaluation_code, record_metric_evaluation_code
---

TASK: Produce a grounded Python function that computes one selected compliance objective from
explicitly supplied data and returns a structured measurement and objective assessment. Generated
source is an artifact, not proof that a metric was computed.

Required before drafting:
- An objective snapshot with its exact catalog metric and condition.
- An explicitly selected project, entity kind (`dataset` or `model`) and entity identity/version.
- Explicit input bindings: data access/interface, relevant columns, labels/predictions, protected
  attributes, metric parameters, and a selector for any map-valued output.
- For model evaluation, an explicit evaluation-data interface, labels/predictions or dataset. A
  model name, metadata, or description alone cannot support model-quality evaluation.

Workflow:
1. Confirm the selected objective and target. Ask for missing bindings rather than inferring them.
   Never select an arbitrary project or infer labels, protected groups, positive labels, averaging,
   threshold, reduction or data location.
2. Call `get_session_evaluation_codes(project)` to retrieve prior project-scoped artifacts when
   continuing an earlier generation; do not reuse an artifact if the objective, metric, entity,
   version, inputs or computation snapshot changed.
3. Call `get_metric_computation(metric_id, entity_kind)` and use the exact returned metric identity,
   applicability, computation section, ordered Python examples, source path and bundle version.
   If the identity is missing/ambiguous, computation is absent, or applicability does not match,
   stop with `unsupported`; do not invent a replacement algorithm.
4. Call `get_evaluation_schema()` before generating code. The evaluator's first argument is the
   assessed entity (or the declared normalized entity interface); its optional evaluation context
   supplies only explicitly bound auxiliary data.
5. Draft one named Python function for the requested objective. Return a JSON-compatible
   `MeasurementEnvelope` with a canonical `MetricResult`, exact objective reference and snapshot,
   target/version, actual computation time, provenance, and determinate/inconclusive assessment.
   Use shared condition semantics; retain metric units and documented value ranges.
   Do not add a publisher, print the result, mutate the entity, install packages, embed credentials,
   or claim code generation measured anything.
6. Return exactly one readiness state:
   - `ready`: complete source, entry point, input/result contracts, dependencies, exact objective and
     metric snapshots, source grounding/hash, and validation status.
   - `needs_input`: list the missing binding(s); include no source code.
   - `unsupported`: explain the unsupported computation/applicability; include no source code.
7. For host-driven generation, call `validate_metric_evaluation_code` on the drafted artifact and
   request. Correct validation errors, then call `record_metric_evaluation_code` only when valid
   and ready. Record the OKF computation path as grounding.
8. Delegated generation is opt-in. Use `generate_metric_evaluation_code` only when the user asks for
   delegated generation and the structured engine is available. It returns the same result-plus-
   assumptions shape and performs static validation/recording; it does not run code.

Validation is syntax/AST and contract checking only. It never imports or executes generated source
and is not a sandbox or semantic certification. The host/service must never execute generated code.
The user may run a reviewed artifact in their own explicitly authorized environment.

Output: the validated artifact, its `ready`/`needs_input`/`unsupported` status, assumptions, and
grounding. Never present an artifact as an evaluated measurement.
