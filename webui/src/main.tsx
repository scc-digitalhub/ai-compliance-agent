import React from "react";
import ReactDOM from "react-dom/client";
import "@/i18n";
import { ComplianceServicesProvider } from "@/compliance-widgets";
import App from "@/App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {/* Omitting `services` uses the module's bundled in-browser mock; pass your own
        EntityService/ComplianceService/AgentService implementations to connect a real backend. */}
    <ComplianceServicesProvider>
      <App />
    </ComplianceServicesProvider>
  </React.StrictMode>,
);
