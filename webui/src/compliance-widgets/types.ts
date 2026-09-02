/** The three entity kinds the compliance widgets support, matching okb "appliesTo" targets. */
export type EntityKind = "project" | "dataset" | "model";

/** Generic JSON object — entity definitions and compliance specs are treated as loosely-typed
 * records edited through the schema-driven form, mirroring how a real backend exchanges plain
 * JSON payloads validated against the OKB JSON Schemas. */
export type JsonRecord = Record<string, unknown>;

export interface EntityRecord {
  id: string;
  name: string;
  [key: string]: unknown;
}

/** Entity definition schema (see schema/entitySchemas.ts) backing each entity kind. */
export const ENTITY_SCHEMA_NAME: Record<EntityKind, string> = {
  project: "ProjectInput",
  dataset: "DatasetInput",
  model: "ModelInput",
};

/** Compliance specification schema (see schema/registry.ts) backing each entity kind. */
export const COMPLIANCE_SCHEMA_NAME: Record<EntityKind, string> = {
  project: "ProjectComplianceSpec",
  dataset: "DataComplianceSpec",
  model: "ModelComplianceSpec",
};
