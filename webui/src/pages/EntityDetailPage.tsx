import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert, Box, Button, CircularProgress, Snackbar, Stack, Tab, Tabs, Typography } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import {
  DatasetComplianceWidget, EntityForm, ModelComplianceWidget, ProjectComplianceWidget,
  useComplianceServices, type EntityKind, type JsonRecord,
} from "@/compliance-widgets";

interface EntityDetailPageProps {
  kind: EntityKind;
}

const COMPLIANCE_WIDGETS: Record<EntityKind, typeof ProjectComplianceWidget> = {
  project: ProjectComplianceWidget,
  dataset: DatasetComplianceWidget,
  model: ModelComplianceWidget,
};

export default function EntityDetailPage({ kind }: EntityDetailPageProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isNew = id === "new";
  const { entityService } = useComplianceServices();

  const [topTab, setTopTab] = useState(0);
  const [loading, setLoading] = useState(!isNew);
  const [entity, setEntity] = useState<JsonRecord>({});
  const [entityId, setEntityId] = useState<string | undefined>(isNew ? undefined : id);
  const [savingEntity, setSavingEntity] = useState(false);
  const [snackbar, setSnackbar] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    setLoading(true);
    entityService.getEntity(kind, id as string).then((e) => {
      setEntity(e ?? {});
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, id]);

  const saveEntity = async () => {
    setSavingEntity(true);
    try {
      if (isNew || !entityId) {
        const created = await entityService.createEntity(kind, entity);
        setEntity(created);
        setEntityId(created.id as string);
        setSnackbar(t("common.savedSuccessfully") as string);
        navigate(`/${kind}s/${created.id}`, { replace: true });
      } else {
        const updated = await entityService.updateEntity(kind, entityId, entity);
        setEntity(updated);
        setSnackbar(t("common.savedSuccessfully") as string);
      }
    } finally {
      setSavingEntity(false);
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  const ComplianceWidget = COMPLIANCE_WIDGETS[kind];

  return (
    <Box>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(`/${kind}s`)} sx={{ mb: 2 }}>
        {t("common.back")}
      </Button>

      <Typography variant="h5" gutterBottom>
        {(entity.name as string) || t("entity.newEntity", { kind: t(`entityKind.${kind}`) })}
      </Typography>

      <Tabs value={topTab} onChange={(_e, v) => setTopTab(v)} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tab label={t("entity.definitionTab")} />
        <Tab label={t("entity.complianceTab")} disabled={!entityId} />
      </Tabs>
      {!entityId && (
        <Alert severity="info" sx={{ mt: 2, mb: 1 }}>
          {t("entity.definitionSectionHelp")}
        </Alert>
      )}
      <Box sx={{ mb: 3 }} />

      {topTab === 0 && (
        <Stack spacing={3}>
          <Typography variant="body2" color="text.secondary">
            {t("entity.definitionSectionHelp")}
          </Typography>
          <EntityForm kind={kind} value={entity} onChange={setEntity} only={kind === "project" ? ["name"] : undefined} />
          <Box>
            <Button variant="contained" startIcon={<SaveIcon />} onClick={saveEntity} disabled={savingEntity}>
              {t("common.save")}
            </Button>
          </Box>
        </Stack>
      )}

      {topTab === 1 && entityId && (
        <ComplianceWidget entityId={entityId} onSaved={() => setSnackbar(t("common.savedSuccessfully") as string)} />
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar(null)} message={snackbar} />
    </Box>
  );
}
