import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Alert, Box, Button, CircularProgress, Divider, Snackbar, Stack, Tab, Tabs, Typography,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import type { EntityKind, JsonRecord } from "@/types/domain";
import { createEntity, getEntity, updateEntity } from "@/services/entityApi";
import { getComplianceSpec, saveComplianceSpec } from "@/services/complianceApi";
import EntityForm from "@/components/entity/EntityForm";
import ProjectComplianceEditor from "@/components/compliance/ProjectComplianceEditor";
import DatasetComplianceEditor from "@/components/compliance/DatasetComplianceEditor";
import ModelComplianceEditor from "@/components/compliance/ModelComplianceEditor";
import AgentAssistPanel from "@/components/compliance/AgentAssistPanel";

interface EntityDetailPageProps {
  kind: EntityKind;
}

export default function EntityDetailPage({ kind }: EntityDetailPageProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isNew = id === "new";

  const [topTab, setTopTab] = useState(0);
  const [loading, setLoading] = useState(!isNew);
  const [entity, setEntity] = useState<JsonRecord>({});
  const [entityId, setEntityId] = useState<string | undefined>(isNew ? undefined : id);
  const [spec, setSpec] = useState<JsonRecord>({});
  const [savingEntity, setSavingEntity] = useState(false);
  const [savingSpec, setSavingSpec] = useState(false);
  const [snackbar, setSnackbar] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    setLoading(true);
    Promise.all([getEntity(kind, id as string), getComplianceSpec(kind, id as string)]).then(([e, s]) => {
      setEntity(e ?? {});
      setSpec(s ?? {});
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, id]);

  const saveEntity = async () => {
    setSavingEntity(true);
    try {
      if (isNew || !entityId) {
        const created = await createEntity(kind, entity);
        setEntity(created);
        setEntityId(created.id as string);
        setSnackbar(t("common.savedSuccessfully") as string);
        navigate(`/${kind}s/${created.id}`, { replace: true });
      } else {
        const updated = await updateEntity(kind, entityId, entity);
        setEntity(updated);
        setSnackbar(t("common.savedSuccessfully") as string);
      }
    } finally {
      setSavingEntity(false);
    }
  };

  const saveSpec = async () => {
    if (!entityId) return;
    setSavingSpec(true);
    try {
      await saveComplianceSpec(kind, entityId, spec);
      setSnackbar(t("common.savedSuccessfully") as string);
    } finally {
      setSavingSpec(false);
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

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
        <Stack spacing={3}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" flexWrap="wrap" gap={2}>
            <AgentAssistPanel kind={kind} entity={entity} currentSpec={spec} onApply={setSpec} />
            <Button variant="contained" startIcon={<SaveIcon />} onClick={saveSpec} disabled={savingSpec}>
              {t("common.save")}
            </Button>
          </Stack>
          <Divider />
          {Object.keys(spec).length === 0 && (
            <Alert severity="info">{t("agent.generateCta")}</Alert>
          )}
          {kind === "project" && <ProjectComplianceEditor spec={spec} onChange={setSpec} />}
          {kind === "dataset" && <DatasetComplianceEditor spec={spec} onChange={setSpec} />}
          {kind === "model" && <ModelComplianceEditor spec={spec} onChange={setSpec} />}
        </Stack>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar(null)} message={snackbar} />
    </Box>
  );
}
