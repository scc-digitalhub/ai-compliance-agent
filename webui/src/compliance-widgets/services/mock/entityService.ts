import { v4 as uuidv4 } from "uuid";
import type { EntityKind, JsonRecord } from "../../types";
import type { EntityService } from "../types";
import { delay, localDb } from "./storage";
import { SEED_DATASETS, SEED_MODELS, SEED_PROJECTS } from "./seed";

const SEEDS: Record<EntityKind, JsonRecord[]> = {
  project: SEED_PROJECTS,
  dataset: SEED_DATASETS,
  model: SEED_MODELS,
};

function loadAll(kind: EntityKind): JsonRecord[] {
  return localDb.read(localDb.entitiesKey(kind), SEEDS[kind]);
}

function saveAll(kind: EntityKind, records: JsonRecord[]): void {
  localDb.write(localDb.entitiesKey(kind), records);
}

/**
 * In-browser mock {@link EntityService}, backed by `localStorage` and seeded with fixture data.
 * Replace with an implementation calling your real backend to swap in production data.
 */
export function createMockEntityService(): EntityService {
  return {
    async listEntities(kind) {
      return delay(loadAll(kind), 300);
    },

    async getEntity(kind, id) {
      return delay(loadAll(kind).find((e) => e.id === id) ?? null, 250);
    },

    async createEntity(kind, data) {
      const all = loadAll(kind);
      const record: JsonRecord = { id: uuidv4(), ...data };
      saveAll(kind, [...all, record]);
      return delay(record, 400);
    },

    async updateEntity(kind, id, data) {
      const all = loadAll(kind);
      const next = all.map((e) => (e.id === id ? { ...data, id } : e));
      saveAll(kind, next);
      return delay({ ...data, id }, 400);
    },

    async deleteEntity(kind, id) {
      saveAll(kind, loadAll(kind).filter((e) => e.id !== id));
      await delay(undefined, 300);
    },
  };
}
