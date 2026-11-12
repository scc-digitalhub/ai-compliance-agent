---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

name: project-context
description: Builds the structured AI compliance context (regulations, requirements, groups, protected attributes, misuse scenarios, risk level, human oversight) for an AI project definition.
allowed-tools: get_compliance_specification get_regulatory_refs get_requirements get_groups get_attributes get_misuse_scenarios get_output_schema validate_project_context record_compliance_analysis
metadata:
  compliance-tools: get_compliance_specification, get_regulatory_refs, get_requirements, get_groups, get_attributes, get_misuse_scenarios, get_output_schema, validate_project_context, record_compliance_analysis
---

TASK: Build the ComplianceContext of the AI project described by the input.
Ground every fact in the OKF tools; use general knowledge only for concepts the bundle lacks and record
that in `assumptions`.

The input is a project definition: name, domain (domain, subdomain, use_case), ai_task, ai_task_value,
goal, purpose, audience, scope (in_scope, out_of_scope), deployment, geography, environment.

Steps:
1. Identify the applicable regulatory frameworks from the geography and domain.
   - Call get_regulatory_refs() (e.g. EU AI Act, GDPR, DSA, NIS2 when relevant).
   - Determine the EU AI Act risk level from the ai_task and domain.

2. Retrieve the normative requirements.
   - Call get_requirements('eu-ai-act') and get_requirements('gdpr').
   - Also check iso-42001-annex-a, dsa, nis2, eba-ml, eu-charter, unesco when relevant.
   - Keep the requirements applicable to the risk level and domain; set applicability_status accordingly.

3. Identify affected and vulnerable groups with get_groups().

4. Identify protected attributes with get_attributes(), based on domain and task.

5. Identify foreseeable misuse with get_misuse_scenarios(), relevant to domain and deployment.

6. Choose a human oversight profile appropriate for the risk level; overseer_roles are actor roles
   (e.g. HUMAN_OVERSIGHT_OPERATOR, DEPLOYER, COMPLIANCE_OWNER).

Rules:
- Copy `id`, names, uris and enum values from tool results (`instance` field); never invent catalog ids.
- Enum fields accept only the values in the output schema. When a value is OTHER, fill the matching
  `*_value` field.
- Put the justification of each judgement in `rationale`.

Host-driven workflow (default):
1. Call get_compliance_specification(kind='project', entity=project.name) before generating. If a
   specification exists, present it and ask whether to re-run; proceed only after the user confirms.
   Continue on not_found. Report other errors and do not silently proceed.
2. Call get_output_schema('project') before generating the result.
3. Call validate_project_context with the original project request and generated output.
4. If invalid, correct the errors and validate again. When valid, call record_compliance_analysis
   with kind='project', the original request, the generated output and `grounding`: the OKF
   concept paths you read (required: recording is refused without them or with paths that are
   not in the bundle). They are stored as the result's provenance.
5. Return the normalized output from the successful validation; do not include tool-call details.

Delegated mode is opt-in. If the user asks for it and analyze_project_context is available, use that
tool instead of generating and validating the result yourself.

Output: the object defined by the output schema (`result` and `assumptions`). Return nothing else:
no narrative, no markdown.
