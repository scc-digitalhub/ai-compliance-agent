import type { JsonRecord } from "../../types";

/** Seed data mirroring src/compliance_agent/data/{projects,datasets,models} sample fixtures. */

export const SEED_PROJECTS: JsonRecord[] = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    name: "AI Loan Approval System",
    domain: "finance",
    subdomain: "retail banking",
    ai_task: "CLASSIFICATION",
    goal: "Automate creditworthiness assessment for retail loan applications.",
    purpose: "Streamline credit decision-making for loan officers",
    audience: "Retail banking customers and loan officers",
    scope_in: ["Credit scoring", "Application screening"],
    scope_out: ["Final lending decision", "Fraud investigation"],
    deployment: "CLOUD",
    geography: ["IT", "EU"],
    environment: "PRODUCTION",
  },
];

export const SEED_DATASETS: JsonRecord[] = [
  {
    id: "22222222-2222-2222-2222-222222222222",
    name: "loan_applications_2023",
    description: "Historical retail loan application records with applicant demographics and credit outcomes.",
    scope: "TRAINING",
    domain: "finance",
    sensitivity: "PII",
    n_records: 120000,
    schema_fields: [
      { name: "applicant_id", dtype: "STRING", sensitivity: "NONE", nullable: false },
      { name: "age", dtype: "INT", sensitivity: "PII", nullable: false },
      { name: "gender", dtype: "STRING", sensitivity: "SENSITIVE", nullable: true },
      { name: "nationality", dtype: "STRING", sensitivity: "SENSITIVE", nullable: true },
      { name: "marital_status", dtype: "STRING", sensitivity: "PII", nullable: true },
      { name: "income_annual", dtype: "FLOAT", sensitivity: "PII", nullable: false },
      { name: "credit_score", dtype: "INT", sensitivity: "PII", nullable: false },
      { name: "loan_amount", dtype: "FLOAT", sensitivity: "NONE", nullable: false },
      { name: "loan_purpose", dtype: "STRING", sensitivity: "NONE", nullable: true },
      { name: "outcome", dtype: "INT", sensitivity: "NONE", nullable: false },
    ],
    known_protected_attributes: ["gender", "nationality", "age", "marital_status"],
  },
];

export const SEED_MODELS: JsonRecord[] = [
  {
    id: "33333333-3333-3333-3333-333333333333",
    name: "credit_xgboost_v2",
    description: "XGBoost binary classifier predicting loan approval probability from applicant financial profile.",
    ai_task: "CLASSIFICATION",
    domain: "finance",
    framework: "XGBOOST",
    output_type: "BINARY_CLASSIFICATION",
    produces_probabilities: true,
    trained_on_sensitive_data: true,
    known_affected_groups: ["retail banking customers", "loan applicants"],
  },
];

/** Pre-generated ProjectComplianceSpec for the seed project, so the UI has something to show
 * on first load without requiring a "Generate with AI" round-trip. */
export const SEED_PROJECT_COMPLIANCE_SPEC: JsonRecord = {
  domain: { domain: "finance", subdomain: "retail banking", use_case: "Retail credit scoring" },
  ai_task: "CLASSIFICATION",
  goal: "Automate creditworthiness assessment for retail loan applications.",
  purpose: "Streamline credit decision-making for loan officers",
  audience: "Retail banking customers and loan officers",
  scope: {
    in_scope: ["Credit scoring", "Application screening"],
    out_of_scope: ["Final lending decision", "Fraud investigation"],
  },
  deployment: "CLOUD",
  context: {
    environment: "PRODUCTION",
    geography: ["IT", "EU"],
    actor_role: "Provider",
    regulations: [{ framework: "EU_AI_ACT", article: "Annex III(5)(b)", version: "2024" }],
    risk_classification: {
      risk_level: "HIGH",
      classification_status: "ASSESSED",
      rationale: "Creditworthiness scoring of natural persons falls under Annex III high-risk use cases.",
    },
    human_oversight: {
      oversight_mode: "HUMAN_IN_THE_LOOP",
      intervention_points: ["OUTPUT_REVIEW", "DECISION_APPROVAL"],
      authority: ["OVERRIDE_OUTPUT", "ESCALATE"],
      availability: "BUSINESS_HOURS",
    },
    protected_attributes: [
      { id: "attr-gender", name: "gender", semantic_type: "GENDER", attribute_role: "PROTECTED_ATTRIBUTE" },
      { id: "attr-nationality", name: "nationality", semantic_type: "NATIONALITY", attribute_role: "PROTECTED_ATTRIBUTE" },
    ],
    requirements: [],
    affected_groups: [],
    vulnerable_groups: [],
    foreseeable_misuse: [],
  },
  objectives: [],
  compliance_status: {
    status: "PENDING_REVIEW",
    assessed_at: new Date().toISOString(),
    assessor: { kind: "AGENT", id: "compliance-agent@ai-compliance" },
    findings: [],
    mitigations: [],
  },
  documentation: { sections: [] },
};
