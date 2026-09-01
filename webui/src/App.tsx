import { Route, BrowserRouter, Routes } from "react-router-dom";
import AppLayout from "@/components/layout/AppLayout";
import Dashboard from "@/pages/Dashboard";
import EntityListPage from "@/pages/EntityListPage";
import EntityDetailPage from "@/pages/EntityDetailPage";
import HelpPage from "@/pages/HelpPage";
import NotFound from "@/pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />

          <Route path="/projects" element={<EntityListPage kind="project" />} />
          <Route path="/projects/:id" element={<EntityDetailPage kind="project" />} />

          <Route path="/datasets" element={<EntityListPage kind="dataset" />} />
          <Route path="/datasets/:id" element={<EntityDetailPage kind="dataset" />} />

          <Route path="/models" element={<EntityListPage kind="model" />} />
          <Route path="/models/:id" element={<EntityDetailPage kind="model" />} />

          <Route path="/help" element={<HelpPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
