import { Box, Divider, List, ListItem, ListItemText, Paper, Typography } from "@mui/material";
import { useTranslate } from "react-admin";

export default function HelpPage() {
  const t = useTranslate();
  return (
    <Box sx={{ maxWidth: 900 }}>
      <Typography variant="h5" gutterBottom>
        {t("help.title")}
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          What this console does
        </Typography>
        <Typography variant="body2" paragraph>
          The AI Compliance Console manages the entities that undergo AI compliance assessment —
          <b> projects</b>, <b>datasets</b> and <b>models</b> — and lets you view and edit the structured
          compliance specification attached to each of them: <code>ProjectComplianceSpec</code>,{" "}
          <code>DataComplianceSpec</code> and <code>ModelComplianceSpec</code>, as defined under{" "}
          <code>okb/schemas/</code> in this repository.
        </Typography>
        <Typography variant="body2" paragraph>
          Every entity has two tabs: <b>Definition</b> (the plain business-level description of the
          project/dataset/model, matching <code>ProjectInput</code> / <code>DatasetInput</code> /{" "}
          <code>ModelInput</code> in <code>src/compliance_agent/api/models.py</code>) and{" "}
          <b>Compliance specification</b> (the OKB-schema-shaped compliance object).
        </Typography>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Compliance specification tabs
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText primary="General" secondary="Domain/task/goal/purpose/scope/deployment for projects; scope/governance/attributes for datasets; no additional fields for models." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Status" secondary="ComplianceStatus: overall status, assessment metadata, findings and mitigation actions." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Requirements (projects only)" secondary="The full ComplianceContext object: environment, geography, regulations, requirements, risk classification, actor role, affected/vulnerable groups, protected attributes, foreseeable misuse, human oversight. Compliance objectives are also shown here, read-only — they are owned/edited at the dataset and model level." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Objectives (datasets and models)" secondary="Fully editable compliance objectives — datasets and models have no ComplianceContext of their own." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Documentation" secondary="Free-form, recursively nested documentation sections (model/data/system cards)." />
          </ListItem>
        </List>
        <Typography variant="body2">
          Each tab groups related fields into accordions. Repeatable sub-entities (regulations, groups,
          misuse scenarios, requirements, objectives, findings, mitigations, document sections…) are
          rendered as add/remove-able accordion lists, generated directly from the JSON Schema
          definitions in <code>okb/schemas/</code> (see <code>src/schema/</code> in this app). For
          projects, the Definition tab only exposes the entity name — the rest of the project
          definition is edited via the compliance spec's General tab. The compliance specification
          is always editable manually, even for a brand-new entity that has no AI-generated content
          yet.
        </Typography>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          AI agent assistance
        </Typography>
        <Typography variant="body2" paragraph>
          Every compliance specification editor exposes two agent actions:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemText primary="Generate with AI" secondary="Drafts a full compliance specification from scratch, based on the entity definition." />
          </ListItem>
          <ListItem>
            <ListItemText primary="Extend with AI" secondary="Suggests additions that only fill empty fields and append new list items — it never overwrites existing edits." />
          </ListItem>
        </List>
        <Typography variant="body2">
          Suggestions are always shown in a preview dialog together with the agent's rationale, and must
          be explicitly applied. This currently calls the bundled mock <code>AgentService</code> (see{" "}
          <code>src/compliance-widgets/services/mock/agentService.ts</code>) standing in for the real
          LangChain-based agent exposed by{" "}
          <code>POST /compliance/{"{context|dataset|model}"}/{"{id}"}</code> in the Python backend.
        </Typography>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Standalone module &amp; mock services
        </Typography>
        <Typography variant="body2" paragraph>
          The Project/Dataset/Model compliance widgets live in{" "}
          <code>src/compliance-widgets/</code>, a self-contained module with no dependency on this
          demo app: it exposes <code>EntityService</code>, <code>ComplianceService</code> and{" "}
          <code>AgentService</code> interfaces, a <code>ComplianceServicesProvider</code> to inject
          implementations of them, and a bundled in-browser mock (backed by <code>localStorage</code>)
          implementing all three so the widgets work out of the box. Function signatures mirror the
          REST resources a real FastAPI backend is expected to expose, so swapping in real{" "}
          <code>fetch</code>-based implementations later requires no changes to the widgets
          themselves — only to the services passed to the provider.
        </Typography>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Internationalization
        </Typography>
        <Typography variant="body2">
          The interface is available in English and Italian (see <code>src/i18n/</code>). Use the
          language switch in the top bar to change it; the choice is remembered across sessions.
        </Typography>
      </Paper>

      <Divider sx={{ my: 2 }} />
      <Typography variant="caption" color="text.secondary">
        See <code>webui/README.md</code> in the repository for developer documentation.
      </Typography>
    </Box>
  );
}
