import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  AppBar, Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, MenuItem, Select,
  Toolbar, Typography,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import ModelTrainingIcon from "@mui/icons-material/ModelTraining";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import GavelIcon from "@mui/icons-material/Gavel";
import { useLocaleState, useTranslate } from "react-admin";
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from "@/i18n";

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
  { to: "/", labelKey: "nav.dashboard", icon: <DashboardIcon /> },
  { to: "/projects", labelKey: "nav.projects", icon: <FolderIcon /> },
  { to: "/datasets", labelKey: "nav.datasets", icon: <DatasetIcon /> },
  { to: "/models", labelKey: "nav.models", icon: <ModelTrainingIcon /> },
  { to: "/help", labelKey: "nav.documentation", icon: <HelpOutlineIcon /> },
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const t = useTranslate();
  const [locale, setLocale] = useLocaleState();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ gap: 1 }}>
          <GavelIcon />
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {t("app.title")}
          </Typography>
          <Select
            size="small"
            value={locale}
            onChange={(e) => setLocale(e.target.value as SupportedLanguage)}
            sx={{ color: "inherit", ".MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.4)" } }}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <MenuItem key={lang} value={lang}>
                {lang.toUpperCase()}
              </MenuItem>
            ))}
          </Select>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <List>
          {NAV_ITEMS.map((item) => {
            const selected = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
            return (
              <ListItemButton key={item.to} component={NavLink} to={item.to} selected={selected}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={t(item.labelKey)} />
              </ListItemButton>
            );
          })}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
}
