import type { EntityKind, JsonRecord } from "../../types";
import { ENTITY_SCHEMA_NAME } from "../../types";
import SchemaForm from "../schemaForm/SchemaForm";

interface EntityFormProps {
  kind: EntityKind;
  value: JsonRecord;
  onChange: (value: JsonRecord) => void;
  /** Restrict the form to a subset of the entity schema's properties. */
  only?: string[];
}

/** Basic entity definition form (project/dataset/model), schema-driven from ENTITY_SCHEMAS. */
export default function EntityForm({ kind, value, onChange, only }: EntityFormProps) {
  return <SchemaForm schemaName={ENTITY_SCHEMA_NAME[kind]} value={value} onChange={onChange} omit={["id"]} only={only} />;
}
