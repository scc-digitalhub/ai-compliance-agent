import { v4 as uuidv4 } from "uuid";
import type { EntityKind, JsonRecord } from "@/types/domain";
import { delay, localDb } from "./storage";
import { SEED_DATASETS, SEED_MODELS, SEED_PROJECTS } from "./seed";

/**
 * Mock implementation of the `/entities/{projects|datasets|models}` REST resource described in
 * src/compliance_agent/api/crud.py. Backed by localStorage so edits survive a page reload.
 *
 * Replace the bodies of these functions with real `fetch(...)` calls against the FastAPI backend
 * once it exposes these endpoints for the frontend; the function signatures are designed to map
 * 1:1 onto that future REST API.
 */

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

export async function listEntities(kind: EntityKind): Promise<JsonRecord[]> {
  return delay(loadAll(kind), 300);
}

export async function getEntity(kind: EntityKind, id: string): Promise<JsonRecord | null> {
  const found = loadAll(kind).find((e) => e.id === id) ?? null;
  return delay(found, 250);
}

export async function createEntity(kind: EntityKind, data: JsonRecord): Promise<JsonRecord> {
  const all = loadAll(kind);
  const record: JsonRecord = { id: uuidv4(), ...data };
  saveAll(kind, [...all, record]);
  return delay(record, 400);
}

export async function updateEntity(kind: EntityKind, id: string, data: JsonRecord): Promise<JsonRecord> {
  const all = loadAll(kind);
  const next = all.map((e) => (e.id === id ? { ...data, id } : e));
  saveAll(kind, next);
  return delay({ ...data, id }, 400);
}

export async function deleteEntity(kind: EntityKind, id: string): Promise<void> {
  const all = loadAll(kind);
  saveAll(kind, all.filter((e) => e.id !== id));
  await delay(undefined, 300);
}
