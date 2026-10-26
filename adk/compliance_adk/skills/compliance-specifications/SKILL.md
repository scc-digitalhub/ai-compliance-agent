---
name: compliance-specifications
description: Stores and retrieves the structured compliance specifications of project, dataset and model entities on the DH platform.
metadata:
  adk_additional_tools:
    - get_compliance_specification
    - save_compliance_specification
---

Use this skill to persist the structured specifications produced by the analyses and to load stored ones.

Kinds, each tied to one entity of the DH platform:
- project: the project description (domain, ai_task, goal, scope, ...) and its compliance context
  (risk classification, requirements, groups, oversight) under `context`.
- dataset: the data compliance specification of a dataset (attributes and objectives).
- model: the model compliance specification of a model (objectives).

Existing or new specification
The analysis tools check the DH platform themselves (identifier: the project, dataset or model name):
1. If a specification is stored, the tool returns it (stored_on_dh, analysis_run false) and loads it into
   the conversation. Present it, say it came from the DH platform, and ask whether to re-run the analysis;
   wait for the answer. Re-run only when they say yes, by calling the analysis tool with rerun=True, then
   offer to save the new result, which replaces the stored one.
2. If none is stored, the tool runs the analysis. Report the result and offer to save it.
To check for a specification without analysing, call get_compliance_specification (not_found means none).

Saving
1. Run the matching analysis first, unless the user supplies the specification themselves.
2. Call save_compliance_specification with the kind and the entity identifier. Omit `specification` to
   store the one analysed in this conversation; pass it only when the user provides or edits one.
3. Saving replaces the stored specification; say so when you report it.

Retrieving
- Call get_compliance_specification with the kind and the entity identifier. The result is also loaded
  into the conversation, so later dataset and model analyses reuse a retrieved project context and
  get_session_analyses shows it.
- Explain a retrieved specification from its content; do not re-run the analysis unless asked.

Rules
- The entity identifier is the one the user gives, otherwise the name of the project, dataset or model
  in the request. Never invent one.
- Datasets and models analysed in this conversation are saved under the name used in the analysis.
- Report an error to the user as it is returned (not_found, invalid_specification, dh_error); never retry by
  fabricating or patching specification content.
