import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import "@/i18n";
import { ComplianceServicesProvider } from "@/compliance-widgets";
import { theme } from "@/theme";
import App from "@/App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Omitting `services` uses the module's bundled in-browser mock; pass your own
          EntityService/ComplianceService/AgentService implementations to connect a real backend. */}
      <ComplianceServicesProvider>
        <App />
      </ComplianceServicesProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
