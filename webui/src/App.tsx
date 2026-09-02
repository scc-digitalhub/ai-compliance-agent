import { Admin, Resource } from "react-admin";
import FolderIcon from "@mui/icons-material/Folder";
import DatasetIcon from "@mui/icons-material/Dataset";
import ModelTrainingIcon from "@mui/icons-material/ModelTraining";
import { useComplianceServices } from "@/compliance-widgets";
import { createComplianceDataProvider } from "@/admin/dataProvider";
import { adminI18nProvider } from "@/admin/i18nProvider";
import { EntityCreate, EntityEdit, EntityList, EntityShow } from "@/admin/EntityResources";
import Dashboard from "@/pages/Dashboard";
import { theme } from "@/theme";

export default function App() {
  const services = useComplianceServices();
  const dataProvider = createComplianceDataProvider(services);

  return (
    <Admin
      dataProvider={dataProvider}
      i18nProvider={adminI18nProvider}
      dashboard={Dashboard}
      theme={theme}
      title="AI Compliance Console"
    >
      <Resource
        name="projects"
        icon={FolderIcon}
        list={EntityList}
        show={() => <EntityShow kind="project" />}
        edit={() => <EntityEdit kind="project" />}
        create={() => <EntityCreate kind="project" />}
      />
      <Resource
        name="datasets"
        icon={DatasetIcon}
        list={EntityList}
        show={() => <EntityShow kind="dataset" />}
        edit={() => <EntityEdit kind="dataset" />}
        create={() => <EntityCreate kind="dataset" />}
      />
      <Resource
        name="models"
        icon={ModelTrainingIcon}
        list={EntityList}
        show={() => <EntityShow kind="model" />}
        edit={() => <EntityEdit kind="model" />}
        create={() => <EntityCreate kind="model" />}
      />
    </Admin>
  );
}
