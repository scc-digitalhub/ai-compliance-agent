import { useState } from "react";
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  Stack, Typography,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { useTranslation } from "react-i18next";
import type { EntityKind, JsonRecord } from "@/types/domain";
import { extendComplianceSpec, generateComplianceSpec, type AgentResult } from "@/services/agentApi";
import { mergeFillGaps } from "@/utils/merge";

interface AgentAssistPanelProps {
  kind: EntityKind;
  entity: JsonRecord;
  currentSpec: JsonRecord;
  onApply: (nextSpec: JsonRecord) => void;
}

type Mode = "generate" | "extend" | null;

/**
 * "Agent interaction" panel: lets the user ask the (mocked) compliance agent to draft a brand new
 * specification from the entity definition, or to extend/fill gaps in the existing one. Suggestions
 * are always previewed (with the agent's rationale) before being applied.
 */
export default function AgentAssistPanel({ kind, entity, currentSpec, onApply }: AgentAssistPanelProps) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<Mode>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState(false);

  const runAgent = async (nextMode: "generate" | "extend") => {
    setMode(nextMode);
    setLoading(true);
    setError(false);
    setResult(null);
    try {
      const res =
        nextMode === "generate"
          ? await generateComplianceSpec(kind, entity)
          : await extendComplianceSpec(kind, entity, currentSpec ?? {});
      setResult(res);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const close = () => {
    setMode(null);
    setResult(null);
    setError(false);
  };

  const apply = () => {
    if (!result) return;
    const next = mode === "generate" ? result.patch : mergeFillGaps(currentSpec ?? {}, result.patch);
    onApply(next);
    close();
  };

  return (
    <Box>
      <Stack direction="row" spacing={1}>
        <Button variant="outlined" size="small" startIcon={<AutoAwesomeIcon />} onClick={() => runAgent("generate")}>
          {t("agent.generate")}
        </Button>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AutoAwesomeIcon />}
          onClick={() => runAgent("extend")}
        >
          {t("agent.extend")}
        </Button>
      </Stack>

      <Dialog open={mode !== null} onClose={close} maxWidth="md" fullWidth>
        <DialogTitle>{mode === "generate" ? t("agent.dialogTitleGenerate") : t("agent.dialogTitleExtend")}</DialogTitle>
        <DialogContent dividers>
          {loading && (
            <Stack alignItems="center" spacing={2} sx={{ py: 4 }}>
              <CircularProgress size={32} />
              <Typography color="text.secondary">{mode === "generate" ? t("agent.generating") : t("agent.extending")}</Typography>
            </Stack>
          )}
          {!loading && error && <Alert severity="error">{t("agent.errorNotice")}</Alert>}
          {!loading && result && (
            <Stack spacing={2}>
              <Alert severity="info" icon={<AutoAwesomeIcon fontSize="inherit" />}>
                <Typography variant="subtitle2" gutterBottom>
                  {t("agent.narrative")}
                </Typography>
                <Typography variant="body2">{result.narrative}</Typography>
              </Alert>
              <Typography variant="caption" color="text.secondary">
                {t("agent.previewHint")}
              </Typography>
              <Box
                component="pre"
                sx={{
                  m: 0,
                  p: 1.5,
                  bgcolor: "grey.100",
                  borderRadius: 1,
                  fontSize: 12,
                  maxHeight: 320,
                  overflow: "auto",
                }}
              >
                {JSON.stringify(result.patch, null, 2)}
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={close}>{t("common.discard")}</Button>
          <Button variant="contained" onClick={apply} disabled={loading || !result}>
            {t("agent.applyAndMerge")}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
