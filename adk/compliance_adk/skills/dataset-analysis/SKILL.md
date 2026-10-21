---
name: dataset-analysis
description: Derives the structured compliance specification (scope, protected attributes, compliance objectives) for an AI dataset.
metadata:
  adk_additional_tools:
    - read_okf_concept
    - get_attributes
    - get_metrics
    - get_requirements
    - get_groups
---

TASK: Derive the data compliance specification of the dataset described by the input.
Ground every fact in the OKF tools; use general knowledge only for concepts the bundle lacks and record
that in `assumptions`.

The input contains `dataset` (name, description, scope, domain, sensitivity, n_records, schema_fields,
sample_records, known_protected_attributes) and optionally `project` and `project_context`. When
`project_context` is present, reuse its requirement ids and consider its protected attributes and
vulnerable groups.

Steps:
1. Identify the dataset role (scope) and sensitivity.
   - If needed, call read_okf_concept('data/DataGovernance.md') and read_okf_concept('data/ConsentSpec.md').

2. Identify protected and sensitive attributes in the schema.
   - Call get_attributes() and match schema field names to known attributes.
   - Include every entry of known_protected_attributes.
   - Flag GDPR Art. 9 special categories.

3. Select data quality, fairness and privacy metrics.
   - get_metrics('data-quality', 'Dataset'); get_metrics('fairness') for the protected attributes;
     get_metrics('privacy') when the data is sensitive.

4. Retrieve the applicable requirements.
   - get_requirements('eu-ai-act', 'art10') for data governance.
   - get_requirements('gdpr') for personal data (Art. 5, 6, 9, 25, 35 as applicable).

5. For each relevant metric propose one objective with: the metric, an acceptance condition,
   a priority (MANDATORY for legal or safety requirements, RECOMMENDED otherwise), a severity and the
   linked requirement ids.

Rules:
- Copy the Metric `instance` returned by get_metrics unchanged into `metric`; respect its range
  (for example completeness is a ratio between 0 and 1, not a percentage).
- Set exactly one condition type per objective: threshold, range, categorical or statistical.
- `requirements` holds only ids returned by get_requirements or present in project_context.
- Output `scope` equals the input dataset scope.
- Enum fields accept only the values in the output schema.

Output: the object defined by the output schema (`result` and `assumptions`). Return nothing else:
no narrative, no markdown.
