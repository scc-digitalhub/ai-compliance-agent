---
name: project-context
description: Given the project metadata information, this skill provides relevant project AI compliance context in a structured format.
metadata:
  adk_additional_tools:
    - get_regulatory_refs
    - get_requirements
    - get_groups
    - get_attributes
    - get_metrics
    - get_misuse_scenarios
---

TASK: Build a ComplianceContext for the  AI project defined by the user.
Prefer OKF tools to retrieve grounded facts; supplement with general knowledge
only for concepts not present in the bundle.

Expected project information should contain:
  - name
  - domain and subdomain: information about application domain
  - ai_task: description of the AI task being performed (e.g., classification)
  - geography: location where the AI system will be deployed
  - goal: the intended objective or purpose of the AI project
  - purpose: the intended use or function of the AI system
  - audience: the intended users or stakeholders of the AI system
  - deployment: details about how and where the AI system will be deployed (e.g., public cloud, on-premises)
  - scope_in and scope_out: the boundaries of the AI system's influence, including what is within the system's control and what lies outside of it

Steps to follow:
1. Identify the deployment geography and applicable regulatory frameworks.
   - Call get_regulatory_refs() to retrieve EU AI Act, GDPR, DSA/NIS2 if relevant.
   - Determine the EU AI Act risk classification based on the AI task and domain.

2. Retrieve relevant normative requirements.
   - Call get_requirements('eu-ai-act') and get_requirements('gdpr').
   - Select the requirements applicable to the project's risk level and domain.
   - Also check iso-42001-annex-a, dsa, nis2, eba-ml as needed.

3. Identify affected and vulnerable groups.
   - Call get_groups() to find groups impacted by the AI task and domain.

4. Identify protected attributes.
   - Call get_attributes() based on the domain and task.

5. Identify foreseeable misuse scenarios.
   - Call get_misuse_scenarios() relevant to the domain and deployment.

6. Suggest a human oversight profile appropriate for the risk level.

7. Synthesise a full compliance analysis covering: applicable regulations,
   key requirements, groups, attributes, misuse risks, oversight, and risk level.
   Include both a narrative explanation and the structured data. 
   
For the structured output, return the following elements:
    - narrative_summary: textual summary of the compliance analysis (text format)
    - regulatory_analysis: analysis of applicable regulations and their implications for the project (text format)
    - risk_analysis: assessment of the project's risk level based on the AI task, domain, and regulatory requirements (text format)
    - oversight_analysis: evaluation of the human oversight measures appropriate for the project's risk level (text format)
    - compliance_context: ComplianceContextOut structure as defined in assets/schema.py filling all required fields as specified.

Example of the structured compliance_context output expected:
```json
{
   "environment": "PRODUCTION",
   "regulations": [
      {
         "framework": "EU_AI_ACT",
         "article": "Article 14",
         "uri": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
         "version": "2024/1689"
      }
   ],
   "geography": [
      "EU"
   ],
   "actor_role": "PROVIDER",
   "requirements": [
      {
         "id": "eu-ai-act-article-14",
         "name": "Human oversight",
         "description": "Provide effective human oversight for the AI system.",
         "source": {
            "framework": "EU_AI_ACT",
            "article": "Article 14",
            "uri": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
            "version": "2024/1689"
         },
         "requirement_text": "The system shall be designed so that it can be effectively overseen by natural persons.",
         "kind": "HUMAN_OVERSIGHT",
         "applicability_status": "APPLICABLE",
         "related_requirements": [
            "eu-ai-act-article-9"
         ]
      }
   ],
   "affected_groups": [
      {
         "name": "Service applicants",
         "description": "People whose applications are evaluated by the AI system.",
         "group_kind": "CUSTOMER",
         "group_role": "DECISION_SUBJECT",
         "vulnerability": "Decisions may affect access to essential services.",
         "rationale": "Model outputs can materially influence application outcomes."
      }
   ],
   "vulnerable_groups": [
      {
         "name": "People with disabilities",
         "description": "Applicants with physical, sensory, cognitive, or other disabilities.",
         "group_kind": "VULNERABLE_GROUP",
         "group_role": "DECISION_SUBJECT",
         "vulnerability": "Accessibility barriers and proxy discrimination may create unequal outcomes.",
         "rationale": "The system must account for accessibility and avoid discriminatory treatment."
      }
   ],
   "protected_attributes": [
      {
         "name": "disability",
         "semantic_type": "PROTECTED_CHARACTERISTIC",
         "attribute_role": "FAIRNESS_EVALUATION",
         "observability": "DECLARED_OR_INFERRED",
         "use_permissions": [
            "FAIRNESS_AUDIT"
         ],
         "rationale": "Monitor for direct and proxy discrimination while restricting operational use."
      }
   ],
   "foreseeable_misuse": [
      {
         "name": "Automated rejection without human review",
         "misuse_kind": "OVER_RELIANCE",
         "intentionality": "UNINTENTIONAL",
         "likelihood": "POSSIBLE",
         "impact": "HIGH",
         "rationale": "Operators may treat model recommendations as final decisions."
      }
   ],
   "risk_classification": {
      "risk_level": "HIGH",
      "classification_status": "PRELIMINARY",
      "rationale": "The system may materially influence access to essential services."
   },
   "human_oversight": {
      "oversight_mode": "HUMAN_ON_THE_LOOP",
      "overseer_roles": [
         "Compliance Officer",
         "Qualified Case Reviewer"
      ],
      "intervention_points": [
         "Before an adverse decision",
         "When confidence is below the approved threshold"
      ],
      "authority": [
         "Override model output",
         "Pause automated processing",
         "Escalate for investigation"
      ],
      "availability": "BUSINESS_HOURS",
      "escalation_channels": [
         "Compliance review queue",
         "Incident response process"
      ],
      "rationale": "Meaningful review and intervention are required before consequential decisions."
   }
}
```
