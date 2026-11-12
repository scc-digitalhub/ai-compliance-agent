---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

name: entity-details
description: Retrieves the details of datasets and models registered on the DH platform, so a compliance analysis can be requested by entity name.
allowed-tools: get_entity_details
metadata:
  compliance-tools: get_entity_details
---

Use this skill when the user refers to a dataset or model by its name on the DH platform, for example
"analyse the dataset applications-2024 in project credit" or
"check the compliance of model credit-model in project credit".

Retrieving
1. Establish the DigitalHub project explicitly from the user's current request or earlier context.
   If missing or ambiguous, ask the user before proceeding; never use an environment default.
   Call get_entity_details with the kind ('dataset' or 'model'), entity name and project argument.
   A full store:// key supplied by the user already identifies the project.
2. The details are kept in the conversation. Later calls return them from the session (source
   'session') without contacting the platform. Call with refresh=True only when the user asks to
   reload, refresh or update the details, or says the entity changed on the platform.
3. Report an error as it is returned (missing_project, not_found, dh_error); never invent details or retry with a
   guessed name.

Analysing a retrieved entity
1. Build the analysis input from the details, copying only what they state:
   - dataset (analyze_dataset): name, description, domain, sensitivity, n_records, schema_fields
     (name, dtype, nullable, description from the schema columns), known_protected_attributes; scope
     (TRAINING, VALIDATION or SUPPORT) when the details or the user state it.
   - model (analyze_model): name, description, ai_task, domain, framework, output_type,
     produces_probabilities, trained_on_sensitive_data, known_affected_groups.
   Details are commonly found under the entity name, `metadata` (description, labels) and `spec`
   (schema, framework, algorithm, parameters).
2. Use the entity name as the input name, so the DH specification check and a later save use the same
   identifier.
3. Required inputs missing from the details (dataset: scope; model: ai_task) are asked to the user,
   never guessed. State any default you assume.
4. Run the analysis following the coordinator rules (project analysis first when it is missing).

Rules
- Reuse the details already in the conversation; do not refresh unless asked.
- Explain where each input value came from (DH details, the user, or an assumed default).
