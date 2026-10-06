import { AppLayout } from "./layouts/AppLayout";
import { Navigate, Route, Routes } from "react-router-dom";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FindingsPage } from "./pages/FindingsPage";
import { RepositoriesPage } from "./pages/RepositoriesPage";
import { AuthPage } from "./pages/AuthPage";
import "./styles.css";

export function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/repositories" element={<RepositoriesPage />} />
        <Route path="/repositories/:repositoryId/analysis" element={<AnalysisPage />} />
        <Route path="/analyses/:analysisId/findings" element={<FindingsPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
