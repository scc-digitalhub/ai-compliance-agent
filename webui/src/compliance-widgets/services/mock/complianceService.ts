import type { EntityKind, JsonRecord } from "../../types";
import type { ComplianceService } from "../types";
import { delay, localDb } from "./storage";
import { SEED_PROJECT_COMPLIANCE_SPEC } from "./seed";

const SEED_SPECS: Partial<Record<EntityKind, Record<string, JsonRecord>>> = {
  project: { "11111111-1111-1111-1111-111111111111": SEED_PROJECT_COMPLIANCE_SPEC },
};

/**
 * In-browser mock {@link ComplianceService}, backed by `localStorage` alongside the entities.
 * Replace with an implementation calling your real backend to swap in production data.
 */
export function createMockComplianceService(): ComplianceService {
  return {
    async getComplianceSpec(kind, entityId) {
      const seeded = SEED_SPECS[kind]?.[entityId] ?? null;
      const spec = localDb.read<JsonRecord | null>(localDb.specKey(kind, entityId), seeded);
      return delay(spec, 300);
    },

    async saveComplianceSpec(kind, entityId, spec) {
      localDb.write(localDb.specKey(kind, entityId), spec);
      return delay(spec, 400);
    },

    async deleteComplianceSpec(kind, entityId) {
      localDb.write(localDb.specKey(kind, entityId), null);
      await delay(undefined, 200);
    },
  };
}
