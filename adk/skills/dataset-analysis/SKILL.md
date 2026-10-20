---
name: dataset-analysis
description: Given dataset metadata, schema, and samples, suggest compliance objectives.
metadata:
  adk_additional_tools:
    - read_okf_concept
    - get_attributes
    - get_metrics
    - get_requirements
    - get_groups
---

TASK: Analyse the compliance requirements for the following AI dataset.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Dataset information is expected to contain
   - name
   - description
   - scope (TRAINING | VALIDATION | SUPPORT)
   - domain
   - sensitivity (NONE | PII | SENSITIVE | RESTRICTED | PROHIBITED)
   - n_records: number of records
   - schema_fields: column definitions
   - sample_records: Up to 3 representative rows
   - known_protected_attributes: Known sensitive field names
   - project: Associated project information (if any)

Steps to follow:
1. Identify the dataset's role (training / validation / test) and sensitivity.
   - Call read_okf_concept('data/DataGovernance.md') and read_okf_concept('data/ConsentSpec.md') if needed.

2. Identify protected and sensitive attributes present in the dataset schema.
   - Call get_attributes() to match schema field names to known AttributeRef instances.
   - Flag GDPR Art. 9 special categories if present.

3. Select relevant data quality and fairness objectives.
   - Call get_metrics('data-quality') to identify applicable data quality metrics.
   - Call get_metrics('fairness') to identify fairness metrics given the protected attributes.
   - Call get_metrics('privacy') if sensitive data is present.

4. Retrieve the applicable requirements.
   - Call get_requirements('eu-ai-act', 'art10') for data governance.
   - Call get_requirements('gdpr') for personal data (Art. 5, 6, 9, 25, 35 as applicable).

5. For each relevant metric, propose a concrete ComplianceObjective with:
   - The metric id and name.
   - An acceptance condition (threshold or range).
   - Priority (MANDATORY for safety/legal requirements, RECOMMENDED otherwise).
   - Linked requirement ids.

6. Provide narrative analysis covering: data quality, privacy, fairness, and
   retention/consent concerns.

7. Synthesise the analysis into a structured JSON representation.

For the structured output, return the following elements:
    - narrative_summary: textual summary of the dataset analysis (text format)
    - data_quality_analysis: textual analysis of the dataset's quality (text format)
    - privacy_analysis: textual analysis of the dataset's privacy aspects (text format)
    - fairness_analysis: textual analysis of the dataset's fairness aspects (text format)
    - data_compliance: DataComplianceOut structure as defined in assets/schema.py filling all required fields as specified.


Example of the structured data_compliance output expected:
```json
{
   "scope": "TRAINING",
   "protected_attributes": [
      {
         "name": "age",
         "semantic_type": "PROTECTED_CHARACTERISTIC",
         "attribute_role": "FAIRNESS_EVALUATION",
         "observability": "DIRECTLY_OBSERVED",
         "use_permissions": [
            "FAIRNESS_AUDIT",
            "BIAS_MONITORING"
         ],
         "rationale": "Age is present in the dataset and must be monitored for disparate outcomes."
      }
   ],
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
