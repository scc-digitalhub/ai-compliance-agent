---
name: model-analysis
description: Derives the structured compliance specification (compliance objectives with metrics and acceptance conditions) for an AI model.
allowed-tools: get_compliance_specification read_okf_concept get_attributes get_metrics get_requirements get_groups get_misuse_scenarios get_output_schema validate_model_compliance record_compliance_analysis
metadata:
  compliance-tools: get_compliance_specification, read_okf_concept, get_attributes, get_metrics, get_requirements, get_groups, get_misuse_scenarios, get_output_schema, validate_model_compliance, record_compliance_analysis
---

TASK: Derive the model compliance specification of the model described by the input.
Ground every fact in the OKF tools; use general knowledge only for concepts the bundle lacks and record
that in `assumptions`.

The input contains `model` (name, description, ai_task, domain, framework, output_type,
produces_probabilities, trained_on_sensitive_data, known_affected_groups) and optionally `project`,
`project_context` and `dataset_compliance`. When `project_context` is present, reuse its requirement
ids and consider its protected attributes, groups and misuse scenarios.

Steps:
1. Determine the applicable concern areas from the AI task:
   - classification or regression: fairness, calibration, performance;
   - generative models: privacy, robustness, explainability;
   - all models: performance, robustness, explainability.

2. Retrieve metrics per concern area with get_metrics(area, 'Model'):
   fairness (decisions about individuals), performance, robustness, explainability,
   calibration (probabilistic outputs), privacy (sensitive training data).

3. Read the metric concept files (read_okf_concept) when you need acceptance thresholds or guidance.

4. Retrieve the requirements to link: get_requirements('eu-ai-act') for Art. 10, 13, 14, 15 as
   applicable, plus any other framework in project_context.

5. Call get_misuse_scenarios() to select adversarial and misuse risks relevant to the model type,
   and cover them with robustness or privacy objectives.

6. For each metric create one objective with a concrete acceptance condition (for example a fairness
   difference at most 0.05, AUC at least 0.85), a priority and severity, and the linked requirement ids.

Rules:
- Copy the Metric `instance` returned by get_metrics unchanged into `metric`; respect its range.
- Set exactly one condition type per objective: threshold, range, categorical or statistical.
- `requirements` holds only ids returned by get_requirements or present in project_context.
- Enum fields accept only the values in the output schema.

Host-driven workflow (default):
1. Call get_compliance_specification(kind='model', entity=model.name) before generating. If a
   specification exists, present it and ask whether to re-run; proceed only after the user confirms.
   Continue on not_found. Report other errors and do not silently proceed.
2. Call get_session_analyses and include available project, project-context and dataset results in
   the analysis request.
3. Call get_output_schema('model') before generating the result.
4. Call validate_model_compliance with the original model analysis request and generated output.
5. If invalid, correct the errors and validate again. When valid, call record_compliance_analysis
   with kind='model', the original request and the generated output.
6. Return the normalized output from the successful validation; do not include tool-call details.

Delegated mode is opt-in. If the user asks for it and analyze_model is available, use that tool
instead of generating and validating the result yourself.

Output: the object defined by the output schema (`result` and `assumptions`). Return nothing else:
no narrative, no markdown.
