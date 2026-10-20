---
name: model-analysis
description: Given model metadata and project requirements, suggest compliance objectives.
metadata:
  adk_additional_tools:
    - read_okf_concept
    - get_attributes
    - get_metrics
    - get_requirements
    - get_groups
---

TASK: Analyse the compliance requirements for the following AI model.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Model information is expected to contain:
- name
- description
- ai_task
- domain
- framework (e.g., PYTORCH, SKLEARN, HUGGINGFACE")
- output_type (BINARY_CLASSIFICATION | MULTI_CLASS | REGRESSION | GENERATION | RANKING)
- produces_probabilities
- trained_on_sensitive_data

Steps to follow:
1. Determine the applicable compliance concern areas based on the AI task:
   - For classification/regression: fairness, calibration, performance.
   - For generative models: privacy, robustness, explainability.
   - For all models: performance, robustness, explainability.

2. Retrieve relevant metrics for each concern area:
   - Call get_metrics('fairness') for models making decisions about individuals.
   - Call get_metrics('performance') for accuracy/recall requirements.
   - Call get_metrics('robustness') for adversarial and distribution-shift risks.
   - Call get_metrics('explainability') for transparency requirements.
   - Call get_metrics('calibration') for probabilistic output models.
   - Call get_metrics('privacy') if trained on sensitive data.

3. Read specific metric concept files to get acceptance thresholds and code.

4. For each metric, create a ComplianceObjective with:
   - Concrete acceptance condition (e.g. EOD ≤ 0.05, AUC ≥ 0.85).
   - Appropriate priority and severity.
   - Links to EU AI Act Art. 10, 13, 14, 15 as applicable.

5. Call get_misuse_scenarios() to identify foreseeable misuse and adversarial risks
   relevant to the model type.

6. Provide narrative analysis covering: fairness, robustness, transparency,
   and calibration concerns.

7. Synthesise the analysis into a structured JSON representation.

For the structured output, return the following elements:
    fairness_analysis: str
    robustness_analysis: str
    transparency_analysis: str
    objectives: list[ComplianceObjectiveOut]


    - narrative_summary: textual summary of the dataset analysis (text format)
    - fairness_analysis: textual analysis of the dataset's fairness aspects (text format)
    - robustness_analysis: textual analysis of the dataset's robustness aspects (text format)
    - transparency_analysis: textual analysis of the dataset's transparency aspects (text format)
    - model_compliance: ModelComplianceOut structure as defined in assets/schema.py filling all required fields as specified.


Example of the structured model_compliance output expected:
```json
{
   "objectives": [
      {
         "name": "Dataset completeness",
         "description": "Ensure required training records contain sufficiently complete values.",
         "metric": {
            "id": "data-quality-completeness",
            "name": "Completeness rate",
            "description": "Proportion of required data values that are present.",
            "kind": "DATA_QUALITY",
            "scale": "RATIO",
            "unit": {
               "symbol": "%",
               "name": "percent"
            },
            "range": {
               "lower": 0.0,
               "upper": 100.0,
               "discrete": false,
               "categories": null
            }
         },
         "condition": {
            "threshold": {
               "operator": "GEQ",
               "value": 95.0
            },
            "range": null
         },
         "priority": "MANDATORY",
         "severity": "HIGH",
         "requirements": [
            "eu-ai-act-art10-data-quality",
            "gdpr-art5-accuracy"
         ],
         "rationale": "Incomplete required fields can reduce model reliability and create uneven error rates."
      },
      {
         "name": "Age-group representation",
         "description": "Keep representation of each evaluated age group within the approved range.",
         "metric": {
            "id": "fairness-group-representation",
            "name": "Group representation rate",
            "description": "Percentage of dataset records belonging to an evaluated group.",
            "kind": "FAIRNESS",
            "scale": "RATIO",
            "unit": {
               "symbol": "%",
               "name": "percent"
            },
            "range": {
               "lower": 0.0,
               "upper": 100.0,
               "discrete": false,
               "categories": [
                  "18-29",
                  "30-49",
                  "50-64",
                  "65+"
               ]
            }
         },
         "condition": {
            "threshold": null,
            "range": {
               "lower": 10.0,
               "upper": 40.0,
               "inclusive": true
            }
         },
         "priority": "RECOMMENDED",
         "severity": "MEDIUM",
         "requirements": [
            "eu-ai-act-art10-representativeness"
         ],
         "rationale": "Adequate representation supports reliable fairness evaluation across age groups."
      }
   ]
}
```
