import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Button, Card, CardActionArea, CardContent, Chip, CircularProgress, IconButton, Stack, Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { useTranslate } from "react-admin";
import { useComplianceServices, type EntityKind, type JsonRecord } from "@/compliance-widgets";
import ConfirmDialog from "@/components/common/ConfirmDialog";

interface EntityListPageProps {
  kind: EntityKind;
}

export default function EntityListPage({ kind }: EntityListPageProps) {
  const t = useTranslate();
  const navigate = useNavigate();
  const { entityService, complianceService } = useComplianceServices();
  const [entities, setEntities] = useState<JsonRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingDelete, setPendingDelete] = useState<JsonRecord | null>(null);

  const load = async () => {
    setLoading(true);
    const data = await entityService.listEntities(kind);
    setEntities(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    await entityService.deleteEntity(kind, pendingDelete.id as string);
    await complianceService.deleteComplianceSpec(kind, pendingDelete.id as string);
    setPendingDelete(null);
    load();
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h5">{t("entity.listTitle", { kind: t(`entityKind.${kind}_plural`) })}</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate(`/${kind}s/new`)}>
          {t("entity.newEntity", { kind: t(`entityKind.${kind}`) })}
        </Button>
      </Stack>

      {loading && <CircularProgress />}

      {!loading && entities.length === 0 && <Typography color="text.secondary">{t("common.noItems")}</Typography>}

      <Stack spacing={1.5}>
        {entities.map((entity) => (
          <Card key={entity.id as string} variant="outlined">
            <Stack direction="row" alignItems="center">
              <CardActionArea onClick={() => navigate(`/${kind}s/${entity.id}`)} sx={{ flexGrow: 1 }}>
                <CardContent>
                  <Typography variant="subtitle1">{entity.name as string}</Typography>
                  {entity.description ? (
                    <Typography variant="body2" color="text.secondary">
                      {entity.description as string}
                    </Typography>
                  ) : null}
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    {entity.domain ? <Chip size="small" label={entity.domain as string} /> : null}
                    {entity.ai_task ? <Chip size="small" label={entity.ai_task as string} /> : null}
                    {entity.scope ? <Chip size="small" label={entity.scope as string} /> : null}
                  </Stack>
                </CardContent>
              </CardActionArea>
              <IconButton aria-label={t("common.delete") as string} onClick={() => setPendingDelete(entity)} sx={{ mr: 1 }}>
                <DeleteOutlineIcon />
              </IconButton>
            </Stack>
          </Card>
        ))}
      </Stack>

      <ConfirmDialog
        open={!!pendingDelete}
        title={t("common.confirmDeleteTitle")}
        message={t("common.confirmDeleteMessage", { name: pendingDelete?.name })}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </Box>
  );
}
