---
name: model-analysis
description: Derives the structured compliance specification (compliance objectives with metrics and acceptance conditions) for an AI model.
metadata:
  adk_additional_tools:
    - read_okf_concept
    - get_attributes
    - get_metrics
    - get_requirements
    - get_groups
    - get_misuse_scenarios
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

Output: the object defined by the output schema (`result` and `assumptions`). Return nothing else:
no narrative, no markdown.
