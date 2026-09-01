import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Box, Card, CardActionArea, CardContent, Grid, Stack, Typography } from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import ModelTrainingIcon from "@mui/icons-material/ModelTraining";
import { useTranslation } from "react-i18next";
import type { EntityKind } from "@/types/domain";
import { listEntities } from "@/services/entityApi";

const CARDS: { kind: EntityKind; icon: JSX.Element }[] = [
  { kind: "project", icon: <FolderIcon fontSize="large" color="primary" /> },
  { kind: "dataset", icon: <DatasetIcon fontSize="large" color="primary" /> },
  { kind: "model", icon: <ModelTrainingIcon fontSize="large" color="primary" /> },
];

export default function Dashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [counts, setCounts] = useState<Record<EntityKind, number>>({ project: 0, dataset: 0, model: 0 });

  useEffect(() => {
    Promise.all(CARDS.map((c) => listEntities(c.kind))).then((results) => {
      setCounts({ project: results[0].length, dataset: results[1].length, model: results[2].length });
    });
  }, []);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t("dashboard.welcome")}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 820 }}>
        {t("dashboard.intro")}
      </Typography>
      <Alert severity="info" sx={{ mb: 3, maxWidth: 820 }}>
        {t("dashboard.mockNotice")}
      </Alert>
      <Grid container spacing={2}>
        {CARDS.map(({ kind, icon }) => (
          <Grid item xs={12} sm={4} key={kind}>
            <Card variant="outlined">
              <CardActionArea onClick={() => navigate(`/${kind}s`)}>
                <CardContent>
                  <Stack spacing={1} alignItems="flex-start">
                    {icon}
                    <Typography variant="h6">{t(`entityKind.${kind}_plural`)}</Typography>
                    <Typography variant="h4">{counts[kind]}</Typography>
                    <Typography variant="body2" color="primary">
                      {t("dashboard.goTo", { kind: t(`entityKind.${kind}_plural`) })}
                    </Typography>
                  </Stack>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
