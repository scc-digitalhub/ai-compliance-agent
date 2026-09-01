import type { EntityKind, JsonRecord } from "@/types/domain";

const PREFIX = "ai-compliance-webui";

function key(kind: EntityKind | "compliance", suffix: EntityKind extends never ? never : string): string {
  return `${PREFIX}.${kind}.${suffix}`;
}

/** Thin wrapper around localStorage, isolated so the mock services can be swapped for real
 * HTTP calls later without touching call sites. */
export const localDb = {
  read<T>(storageKey: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return fallback;
      return JSON.parse(raw) as T;
    } catch {
      return fallback;
    }
  },
  write<T>(storageKey: string, value: T): void {
    localStorage.setItem(storageKey, JSON.stringify(value));
  },
  entitiesKey(kind: EntityKind): string {
    return key(kind, "entities");
  },
  specKey(kind: EntityKind, id: string): string {
    return key("compliance", `${kind}.${id}`);
  },
};

/** Simulated network/agent latency so loading states are visible, like a real API. */
export function delay<T>(value: T, ms = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export type JsonRecordMap = Record<string, JsonRecord>;
