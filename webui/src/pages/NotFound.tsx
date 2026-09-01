import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <Box>
      <Typography variant="h5">404</Typography>
      <Typography color="text.secondary">{t("common.noItems")}</Typography>
    </Box>
  );
}
