import { useEffect, useState, type ComponentType } from "react";
import { Alert, Button, CircularProgress, Divider, Stack } from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import type { EntityKind, JsonRecord } from "../../types";
import { useComplianceServices } from "../../services/context";
import AgentAssistPanel from "../compliance/AgentAssistPanel";

export interface ComplianceWidgetProps {
  /** ID of the project/dataset/model entity whose compliance specification this widget edits. */
  entityId: string;
  /** Called after the specification has been successfully saved. */
  onSaved?: (spec: JsonRecord) => void;
}

interface ComplianceEditorProps {
  spec: JsonRecord;
  onChange: (spec: JsonRecord) => void;
}

/**
 * Builds a self-contained "smart" compliance widget for one entity kind: fetches the entity
 * definition + compliance spec via the injected services (see `ComplianceServicesProvider`),
 * offers AI generate/extend assistance, renders the given (controlled) editor component, and
 * saves changes back through the services. Used to build `ProjectComplianceWidget`,
 * `DatasetComplianceWidget` and `ModelComplianceWidget`.
 */
export function createComplianceWidget(kind: EntityKind, Editor: ComponentType<ComplianceEditorProps>) {
  return function ComplianceWidget({ entityId, onSaved }: ComplianceWidgetProps) {
    const { t } = useTranslation();
    const { entityService, complianceService } = useComplianceServices();
    const [entity, setEntity] = useState<JsonRecord>({});
    const [spec, setSpec] = useState<JsonRecord>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
      let cancelled = false;
      setLoading(true);
      Promise.all([entityService.getEntity(kind, entityId), complianceService.getComplianceSpec(kind, entityId)]).then(
        ([fetchedEntity, fetchedSpec]) => {
          if (cancelled) return;
          setEntity(fetchedEntity ?? {});
          setSpec(fetchedSpec ?? {});
          setLoading(false);
        },
      );
      return () => {
        cancelled = true;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [entityId]);

    const save = async () => {
      setSaving(true);
      try {
        const saved = await complianceService.saveComplianceSpec(kind, entityId, spec);
        onSaved?.(saved);
      } finally {
        setSaving(false);
      }
    };

    if (loading) {
      return <CircularProgress />;
    }

    return (
      <Stack spacing={3}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" flexWrap="wrap" gap={2}>
          <AgentAssistPanel kind={kind} entity={entity} currentSpec={spec} onApply={setSpec} />
          <Button variant="contained" startIcon={<SaveIcon />} onClick={save} disabled={saving}>
            {t("common.save")}
          </Button>
        </Stack>
        <Divider />
        {Object.keys(spec).length === 0 && <Alert severity="info">{t("agent.generateCta")}</Alert>}
        <Editor spec={spec} onChange={setSpec} />
      </Stack>
    );
  };
}
