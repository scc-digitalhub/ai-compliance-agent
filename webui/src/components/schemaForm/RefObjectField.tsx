import { useEffect } from "react";
import { Accordion, AccordionDetails, AccordionSummary, Box, Button, IconButton, Stack, Typography } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";
import { useTranslation } from "react-i18next";
import type { JsonRecord } from "@/types/domain";
import { createDefaultForSchema } from "@/schema/resolver";
import SchemaForm from "./SchemaForm";

interface RefObjectFieldProps {
  label: string;
  schemaName: string;
  value: JsonRecord | undefined;
  onChange: (value: JsonRecord | undefined) => void;
  required?: boolean;
  description?: string;
}

/** Renders a single nested `$ref` object property as a collapsible "subsection" accordion. */
export default function RefObjectField({ label, schemaName, value, onChange, required, description }: RefObjectFieldProps) {
  const { t } = useTranslation();

  // Required nested objects are always materialized so the user can fill them in immediately.
  useEffect(() => {
    if (required && !value) {
      onChange(createDefaultForSchema(schemaName));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [required, value, schemaName]);

  if (!value) {
    if (required) {
      return null;
    }
    return (
      <Button size="small" startIcon={<AddIcon />} onClick={() => onChange(createDefaultForSchema(schemaName))} sx={{ alignSelf: "flex-start" }}>
        {t("form.addSubsection", { label })}
      </Button>
    );
  }

  return (
    <Accordion defaultExpanded disableGutters variant="outlined">
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: "100%", pr: 1 }}>
          <Box>
            <Typography variant="subtitle2">{label}</Typography>
            {description && (
              <Typography variant="caption" color="text.secondary">
                {description}
              </Typography>
            )}
          </Box>
          {!required && (
            <IconButton
              component="span"
              size="small"
              aria-label={t("form.removeSubsection", { label }) as string}
              onClick={(e) => {
                e.stopPropagation();
                onChange(undefined);
              }}
            >
              <DeleteOutlineIcon fontSize="small" />
            </IconButton>
          )}
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <SchemaForm schemaName={schemaName} value={value} onChange={(next) => onChange(next)} />
      </AccordionDetails>
    </Accordion>
  );
}
