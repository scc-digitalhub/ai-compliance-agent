import { useFormContext, useWatch } from "react-hook-form";
import {
  Create,
  Datagrid,
  Edit,
  EditButton,
  List,
  SearchInput,
  Show,
  ShowButton,
  SimpleForm,
  TabbedShowLayout,
  TextField,
  TopToolbar,
  useRecordContext,
  useTranslate,
} from "react-admin";
import { Box, Stack, Typography } from "@mui/material";
import {
  DatasetComplianceWidget,
  EntityForm,
  ModelComplianceWidget,
  ProjectComplianceWidget,
  type ComplianceWidgetProps,
  type EntityKind,
  type JsonRecord,
} from "@/compliance-widgets";

interface EntityResourceProps {
  kind: EntityKind;
}

const COMPLIANCE_WIDGETS: Record<EntityKind, React.ComponentType<ComplianceWidgetProps>> = {
  project: ProjectComplianceWidget,
  dataset: DatasetComplianceWidget,
  model: ModelComplianceWidget,
};

const listFilters = [<SearchInput key="q" source="q" alwaysOn />];

export function EntityList() {
  return (
    <List filters={listFilters} sort={{ field: "name", order: "ASC" }}>
      <Datagrid rowClick="show">
        <TextField source="name" />
        <TextField source="description" />
        <TextField source="domain" />
        <TextField source="scope" />
        <ShowButton />
        <EditButton />
      </Datagrid>
    </List>
  );
}

function ComplianceWidgetForRecord({ kind }: EntityResourceProps) {
  const record = useRecordContext();
  if (!record) return null;
  const ComplianceWidget = COMPLIANCE_WIDGETS[kind];
  return <ComplianceWidget entityId={String(record.id)} />;
}

function ShowActions() {
  const t = useTranslate();
  return (
    <TopToolbar>
      <EditButton label={t("common.edit")} />
    </TopToolbar>
  );
}

function EditActions() {
  const t = useTranslate();
  return (
    <TopToolbar>
      <ShowButton label={t("common.view")} />
    </TopToolbar>
  );
}

function EntityInputs({ kind }: EntityResourceProps) {
  const values = useWatch() as JsonRecord;
  const { setValue } = useFormContext();

  return (
    <EntityForm
      kind={kind}
      value={values ?? {}}
      onChange={(next) => {
        Object.entries(next).forEach(([key, value]) => setValue(key, value, { shouldDirty: true }));
      }}
    />
  );
}

export function EntityShow({ kind }: EntityResourceProps) {
  const t = useTranslate();
  return (
    <Show actions={<ShowActions />}>
      <TabbedShowLayout>
        <TabbedShowLayout.Tab label={t("entity.definitionTab")}>
          <TextField source="name" />
          <TextField source="description" />
          <TextField source="domain" />
          <TextField source="scope" />
        </TabbedShowLayout.Tab>
        <TabbedShowLayout.Tab label={t("entity.complianceTab")} path="compliance">
          <ComplianceWidgetForRecord kind={kind} />
        </TabbedShowLayout.Tab>
      </TabbedShowLayout>
    </Show>
  );
}

export function EntityEdit({ kind }: EntityResourceProps) {
  const t = useTranslate();
  return (
    <Edit actions={<EditActions />} mutationMode="pessimistic">
      <SimpleForm>
        <Stack spacing={3} sx={{ width: "100%" }}>
          <Typography variant="h6">{t("entity.definitionTab")}</Typography>
          <EntityInputs kind={kind} />
        </Stack>
      </SimpleForm>
    </Edit>
  );
}

export function EntityCreate({ kind }: EntityResourceProps) {
  const t = useTranslate();
  return (
    <Create redirect="show">
      <SimpleForm>
        <Box sx={{ width: "100%" }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {t("entity.definitionTab")}
          </Typography>
          <EntityInputs kind={kind} />
        </Box>
      </SimpleForm>
    </Create>
  );
}