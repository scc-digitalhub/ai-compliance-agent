import type { EntityKind, JsonRecord } from "@/types/domain";
import { delay, localDb } from "./storage";
import { SEED_PROJECT_COMPLIANCE_SPEC } from "./seed";

/**
 * Mock implementation of the (not-yet-implemented) compliance specification resource, e.g.
 * `GET|PUT /compliance-spec/{project|dataset|model}/{id}`. Persisted alongside entities in
 * localStorage. Swap for real HTTP calls once the backend exposes this resource.
 */

const SEED_SPECS: Partial<Record<EntityKind, Record<string, JsonRecord>>> = {
  project: { "11111111-1111-1111-1111-111111111111": SEED_PROJECT_COMPLIANCE_SPEC },
};

export async function getComplianceSpec(kind: EntityKind, entityId: string): Promise<JsonRecord | null> {
  const seeded = SEED_SPECS[kind]?.[entityId] ?? null;
  const spec = localDb.read<JsonRecord | null>(localDb.specKey(kind, entityId), seeded);
  return delay(spec, 300);
}

export async function saveComplianceSpec(kind: EntityKind, entityId: string, spec: JsonRecord): Promise<JsonRecord> {
  localDb.write(localDb.specKey(kind, entityId), spec);
  return delay(spec, 400);
}

export async function deleteComplianceSpec(kind: EntityKind, entityId: string): Promise<void> {
  localDb.write(localDb.specKey(kind, entityId), null);
  await delay(undefined, 200);
}
