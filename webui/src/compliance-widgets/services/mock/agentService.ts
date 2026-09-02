import { v4 as uuidv4 } from "uuid";
import type { EntityKind, JsonRecord } from "../../types";
import type { AgentResult, AgentService } from "../types";
import { delay } from "./storage";

/**
 * In-browser mock {@link AgentService}. Stands in for a real LangChain-based agent exposed by
 * `POST /compliance/{context|dataset|model}/{id}` (see src/compliance_agent/agent/agent.py).
 *
 * Applies a handful of deterministic heuristics over the entity definition to draft a plausible
 * compliance specification fragment, plus a short narrative explaining the reasoning — mirroring
 * the shape of the real endpoints' `narrative_summary` / analysis fields.
 *
 * Replace with an implementation calling your real backend; keep the same `{ narrative, patch }`
 * return contract for a drop-in swap.
 */

const HIGH_RISK_DOMAINS = [
  "finance", "healthcare", "justice", "education", "employment",
  "law_enforcement", "migration", "critical_infrastructure", "biometric", "insurance",
];

const SEMANTIC_TYPE_GUESS: Record<string, string> = {
  gender: "GENDER",
  sex: "SEX",
  age: "AGE",
  nationality: "NATIONALITY",
  ethnicity: "RACE_ETHNICITY",
  race: "RACE_ETHNICITY",
  religion: "RELIGION",
  disability: "DISABILITY",
  health: "HEALTH_STATUS",
  location: "LOCATION",
  income: "SOCIOECONOMIC_STATUS",
  marital_status: "OTHER",
  education: "EDUCATION",
  employment_status: "EMPLOYMENT_STATUS",
  language: "LANGUAGE",
};

function guessSemanticType(attributeName: string): string {
  const key = attributeName.toLowerCase();
  for (const [needle, semanticType] of Object.entries(SEMANTIC_TYPE_GUESS)) {
    if (key.includes(needle)) return semanticType;
  }
  return "OTHER";
}

function isHighRisk(domain: string | undefined): boolean {
  return !!domain && HIGH_RISK_DOMAINS.includes(domain.toLowerCase());
}

function fairnessObjective(): JsonRecord {
  return {
    name: "Demographic parity difference",
    description: "Difference in positive outcome rate between protected and reference groups must stay within tolerance.",
    metric: {
      id: uuidv4(),
      name: "demographic_parity_difference",
      kind: "PRIMITIVE",
      scale: "RATIO",
      unit: { symbol: "Δ", name: "rate difference" },
      range: { lower: -1, upper: 1 },
    },
    condition: { threshold: { operator: "LEQ", value: 0.1 } },
    priority: "MANDATORY",
    severity: "HIGH",
    requirements: [],
  };
}

function robustnessObjective(): JsonRecord {
  return {
    name: "Adversarial robustness score",
    description: "Model accuracy under bounded adversarial perturbation must not degrade below tolerance.",
    metric: {
      id: uuidv4(),
      name: "adversarial_robustness_score",
      kind: "PRIMITIVE",
      scale: "RATIO",
      unit: { symbol: "%", name: "accuracy retained" },
      range: { lower: 0, upper: 1 },
    },
    condition: { threshold: { operator: "GEQ", value: 0.85 } },
    priority: "RECOMMENDED",
    severity: "MEDIUM",
    requirements: [],
  };
}

function transparencyObjective(): JsonRecord {
  return {
    name: "Decision explanation availability",
    description: "Individual decisions must be accompanied by a human-readable explanation on request.",
    metric: {
      id: uuidv4(),
      name: "explanation_coverage",
      kind: "PRIMITIVE",
      scale: "RATIO",
      unit: { symbol: "%", name: "decisions covered" },
      range: { lower: 0, upper: 1 },
    },
    condition: { threshold: { operator: "GEQ", value: 0.99 } },
    priority: "MANDATORY",
    severity: "HIGH",
    requirements: [],
  };
}

function calibrationObjective(): JsonRecord {
  return {
    name: "Probability calibration error",
    description: "Predicted probabilities must be well-calibrated against observed outcome frequencies.",
    metric: {
      id: uuidv4(),
      name: "expected_calibration_error",
      kind: "PRIMITIVE",
      scale: "RATIO",
      unit: { symbol: "ECE", name: "expected calibration error" },
      range: { lower: 0, upper: 1 },
    },
    condition: { threshold: { operator: "LEQ", value: 0.05 } },
    priority: "RECOMMENDED",
    severity: "MEDIUM",
    requirements: [],
  };
}

function privacyObjective(): JsonRecord {
  return {
    name: "Membership inference risk",
    description: "Susceptibility of the model to membership-inference attacks must remain below tolerance.",
    metric: {
      id: uuidv4(),
      name: "membership_inference_advantage",
      kind: "PRIMITIVE",
      scale: "RATIO",
      unit: { symbol: "adv.", name: "attacker advantage" },
      range: { lower: 0, upper: 1 },
    },
    condition: { threshold: { operator: "LEQ", value: 0.1 } },
    priority: "MANDATORY",
    severity: "HIGH",
    requirements: [],
  };
}

function baseComplianceStatus(): JsonRecord {
  return {
    status: "PENDING_REVIEW",
    assessed_at: new Date().toISOString(),
    assessor: { kind: "AGENT", id: "compliance-agent@ai-compliance" },
    findings: [],
    mitigations: [],
  };
}

function draftDocumentationSection(title: string, content: string): JsonRecord {
  return { title, content, format: "OTHER", subsections: [], reports: [] };
}

// ── Project ──────────────────────────────────────────────────────────────────

function draftProjectSpec(entity: JsonRecord): AgentResult {
  const domain = String(entity.domain ?? "");
  const highRisk = isHighRisk(domain);
  const geography = Array.isArray(entity.geography) && entity.geography.length ? entity.geography : ["EU"];

  const patch: JsonRecord = {
    domain: { domain: domain || "unspecified", subdomain: entity.subdomain ?? "", use_case: entity.goal ?? "" },
    ai_task: entity.ai_task ?? "OTHER",
    goal: entity.goal ?? "",
    purpose: entity.purpose ?? "",
    audience: entity.audience ?? "",
    scope: {
      in_scope: Array.isArray(entity.scope_in) ? entity.scope_in : [],
      out_of_scope: Array.isArray(entity.scope_out) ? entity.scope_out : [],
    },
    deployment: entity.deployment ?? "CLOUD",
    context: {
      environment: entity.environment ?? "PRODUCTION",
      geography,
      actor_role: "Provider",
      regulations: [
        {
          framework: "EU_AI_ACT",
          article: highRisk ? "Annex III (high-risk use case)" : "Art. 52 (transparency obligations)",
          version: "2024",
        },
      ],
      risk_classification: {
        risk_level: highRisk ? "HIGH" : "LIMITED",
        classification_status: "PRELIMINARY",
        rationale: highRisk
          ? `Automated decision-making in the "${domain}" domain typically falls under an EU AI Act Annex III high-risk category.`
          : `No high-risk indicator was found for the "${domain || "unspecified"}" domain; classified as limited risk pending review.`,
      },
      human_oversight: {
        oversight_mode: highRisk ? "HUMAN_IN_THE_LOOP" : "POST_HOC_REVIEW",
        intervention_points: highRisk ? ["OUTPUT_REVIEW", "DECISION_APPROVAL"] : ["OUTPUT_REVIEW"],
        authority: ["OVERRIDE_OUTPUT", "ESCALATE"],
        availability: "BUSINESS_HOURS",
      },
      protected_attributes: [],
      affected_groups: [],
      vulnerable_groups: [],
      foreseeable_misuse: [
        {
          id: uuidv4(),
          name: "Automation bias",
          misuse_kind: "AUTOMATION_BIAS",
          likelihood: "POSSIBLE",
          impact: "MEDIUM",
          rationale: "Operators may over-rely on system output without applying independent judgement.",
        },
      ],
      requirements: [],
    },
    objectives: [transparencyObjective(), ...(highRisk ? [fairnessObjective()] : [])],
    compliance_status: baseComplianceStatus(),
    documentation: {
      sections: [
        draftDocumentationSection(
          "Purpose and intended use",
          `${entity.name ?? "This project"} aims to: ${entity.goal ?? "(goal not provided)"}.`,
        ),
      ],
    },
  };

  const narrative =
    `Analyzed project "${entity.name}" in domain "${domain || "unspecified"}". ` +
    `${highRisk ? "This domain is commonly associated with high-risk AI systems under the EU AI Act (Annex III), so a HIGH risk classification and human-in-the-loop oversight are proposed." : "No high-risk indicator was detected for this domain; a LIMITED risk classification is proposed pending manual review."} ` +
    `Deployment geography was set to ${geography.join(", ")}, and a starter documentation section plus a transparency objective were drafted.`;

  return { narrative, patch };
}

// ── Dataset ──────────────────────────────────────────────────────────────────

function draftDatasetSpec(entity: JsonRecord): AgentResult {
  const knownAttrs: string[] = Array.isArray(entity.known_protected_attributes) ? (entity.known_protected_attributes as string[]) : [];
  const attributes = knownAttrs.map((attrName) => ({
    id: uuidv4(),
    name: attrName,
    semantic_type: guessSemanticType(attrName),
    attribute_role: "PROTECTED_ATTRIBUTE",
    observability: "DIRECT",
    use_permissions: ["FAIRNESS_TESTING", "MONITORING"],
  }));

  const sensitivity = entity.sensitivity ?? "NONE";

  const patch: JsonRecord = {
    scope: entity.scope ?? "TRAINING",
    governance: {
      sensitivity,
      retention: {
        applies_to: ["TRAINING_DATA"],
        retention_basis: "PURPOSE_NECESSITY",
        purposes: ["TRAINING", "BIAS_DETECTION"],
        justification: "Retained for the duration of model training and periodic bias re-evaluation.",
      },
      consent:
        sensitivity === "PII" || sensitivity === "SENSITIVE"
          ? { consent_required: true, consent_basis: "GDPR_ARTICLE_6_1_A", purposes: ["TRAINING", "BIAS_DETECTION"] }
          : { consent_required: false },
    },
    attributes,
    objectives: attributes.length > 0 ? [fairnessObjective()] : [],
    compliance_status: baseComplianceStatus(),
    documentation: {
      sections: [
        draftDocumentationSection(
          "Dataset overview",
          `${entity.name ?? "This dataset"} contains ${entity.n_records ?? "an unspecified number of"} records used for ${String(entity.scope ?? "TRAINING").toLowerCase()}.`,
        ),
      ],
    },
  };

  const narrative =
    `Analyzed dataset "${entity.name}" (sensitivity: ${sensitivity}). ` +
    `${attributes.length > 0 ? `Mapped ${attributes.length} known protected attribute(s) (${knownAttrs.join(", ")}) to AttributeRef entries flagged for fairness testing and monitoring, and proposed a demographic parity objective.` : "No known protected attributes were declared; consider reviewing the schema for potential proxies."} ` +
    `${sensitivity === "PII" || sensitivity === "SENSITIVE" ? "Because the data is personal/sensitive, a consent specification was drafted under GDPR Art. 6(1)(a)." : ""}`;

  return { narrative, patch };
}

// ── Model ────────────────────────────────────────────────────────────────────

function draftModelSpec(entity: JsonRecord): AgentResult {
  const objectives: JsonRecord[] = [transparencyObjective(), calibrationObjective()];
  if (entity.trained_on_sensitive_data) objectives.unshift(fairnessObjective());
  objectives.push(robustnessObjective());
  if (entity.trained_on_sensitive_data) objectives.push(privacyObjective());

  const patch: JsonRecord = {
    objectives,
    compliance_status: baseComplianceStatus(),
    documentation: {
      sections: [
        draftDocumentationSection(
          "Model summary",
          `${entity.name ?? "This model"} (${entity.framework ?? "unknown framework"}) performs ${String(entity.ai_task ?? "an AI task").toLowerCase()} with output type ${entity.output_type ?? "unspecified"}.`,
        ),
      ],
    },
  };

  const narrative =
    `Analyzed model "${entity.name}" (${entity.ai_task ?? "unspecified task"}, ${entity.framework ?? "unknown framework"}). ` +
    `Proposed ${objectives.length} compliance objectives covering transparency, calibration and robustness` +
    `${entity.trained_on_sensitive_data ? ", plus fairness and membership-inference privacy objectives because the model was trained on sensitive data." : "."}`;

  return { narrative, patch };
}

const DRAFTERS: Record<EntityKind, (entity: JsonRecord) => AgentResult> = {
  project: draftProjectSpec,
  dataset: draftDatasetSpec,
  model: draftModelSpec,
};

/** In-browser mock {@link AgentService}. See module doc comment above. */
export function createMockAgentService(): AgentService {
  return {
    async generateComplianceSpec(kind, entity) {
      const result = DRAFTERS[kind](entity);
      return delay(result, 900 + Math.round(Math.random() * 400));
    },

    async extendComplianceSpec(kind, entity, _currentSpec) {
      const result = DRAFTERS[kind](entity);
      const narrative = `${result.narrative} These suggestions will only fill in missing fields and append new list items — your existing edits are preserved.`;
      return delay({ ...result, narrative }, 900 + Math.round(Math.random() * 400));
    },
  };
}
