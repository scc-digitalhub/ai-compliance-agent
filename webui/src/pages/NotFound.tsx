import { Box, Typography } from "@mui/material";
import { useTranslate } from "react-admin";

export default function NotFound() {
  const t = useTranslate();
  return (
    <Box>
      <Typography variant="h5">404</Typography>
      <Typography color="text.secondary">{t("common.noItems")}</Typography>
    </Box>
  );
}
