import { useState } from "react";
import { Box, TextField, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { JsonRecord } from "@/types/domain";

interface JsonFieldProps {
  label: string;
  value: JsonRecord | undefined;
  onChange: (value: JsonRecord) => void;
}

/** Free-form JSON editor for schema-less `object` properties (e.g. DocumentSection.specification). */
export default function JsonField({ label, value, onChange }: JsonFieldProps) {
  const { t } = useTranslation();
  const [text, setText] = useState(() => JSON.stringify(value ?? {}, null, 2));
  const [error, setError] = useState<string | null>(null);

  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <TextField
        fullWidth
        multiline
        minRows={4}
        size="small"
        value={text}
        error={!!error}
        helperText={error ?? " "}
        onChange={(e) => {
          setText(e.target.value);
          try {
            const parsed = JSON.parse(e.target.value || "{}");
            setError(null);
            onChange(parsed);
          } catch {
            setError(t("form.invalidJson") as string);
          }
        }}
        sx={{ fontFamily: "monospace" }}
      />
    </Box>
  );
}
