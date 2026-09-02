import type { DataProvider, RaRecord } from "react-admin";
import type { ComplianceWidgetServices, EntityKind, JsonRecord } from "@/compliance-widgets";

const RESOURCE_KIND: Record<string, EntityKind> = {
  projects: "project",
  datasets: "dataset",
  models: "model",
};

function getKind(resource: string): EntityKind {
  const kind = RESOURCE_KIND[resource];
  if (!kind) throw new Error(`Unknown resource: ${resource}`);
  return kind;
}

function asRecord(value: JsonRecord): RaRecord {
  return value as RaRecord;
}

export function createComplianceDataProvider({ entityService, complianceService }: ComplianceWidgetServices): DataProvider {
  const getList = async (resource: string, params: any) => {
      const records = await entityService.listEntities(getKind(resource));
      const query = String(params.filter?.q ?? "").toLocaleLowerCase();
      const filtered = query
        ? records.filter((record) => JSON.stringify(record).toLocaleLowerCase().includes(query))
        : records;
      const { field, order } = params.sort;
      const sorted = [...filtered].sort((left, right) => {
        const result = String(left[field] ?? "").localeCompare(String(right[field] ?? ""));
        return order === "ASC" ? result : -result;
      });
      const start = (params.pagination.page - 1) * params.pagination.perPage;
      return {
        data: sorted.slice(start, start + params.pagination.perPage).map(asRecord),
        total: sorted.length,
      };
  };

  const provider = {
    getList,

    async getOne(resource: string, params: any) {
      const record = await entityService.getEntity(getKind(resource), String(params.id));
      if (!record) throw new Error(`Record ${params.id} was not found`);
      return { data: asRecord(record) };
    },

    async getMany(resource: string, params: any) {
      const records = await entityService.listEntities(getKind(resource));
      return { data: records.filter((record) => params.ids.includes(record.id as string)).map(asRecord) };
    },

    async getManyReference(resource: string, params: any) {
      return getList(resource, {
        ...params,
        filter: { ...params.filter, [params.target]: params.id },
      });
    },

    async create(resource: string, params: any) {
      const record = await entityService.createEntity(getKind(resource), params.data as JsonRecord);
      return { data: asRecord(record) };
    },

    async update(resource: string, params: any) {
      const record = await entityService.updateEntity(getKind(resource), String(params.id), params.data as JsonRecord);
      return { data: asRecord(record) };
    },

    async updateMany(resource: string, params: any) {
      await Promise.all(
        params.ids.map((id: string | number) =>
          entityService.updateEntity(getKind(resource), String(id), params.data as JsonRecord),
        ),
      );
      return { data: params.ids };
    },

    async delete(resource: string, params: any) {
      const kind = getKind(resource);
      const previous = params.previousData ?? (await entityService.getEntity(kind, String(params.id)));
      await Promise.all([
        entityService.deleteEntity(kind, String(params.id)),
        complianceService.deleteComplianceSpec(kind, String(params.id)),
      ]);
      return { data: asRecord(previous ?? { id: params.id }) };
    },

    async deleteMany(resource: string, params: any) {
      const kind = getKind(resource);
      await Promise.all(
        params.ids.flatMap((id: string | number) => [
          entityService.deleteEntity(kind, String(id)),
          complianceService.deleteComplianceSpec(kind, String(id)),
        ]),
      );
      return { data: params.ids };
    },
  };

  return provider as DataProvider;
}