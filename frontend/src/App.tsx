import { AppLayout } from "./layouts/AppLayout";
import { RepositoriesPage } from "./pages/RepositoriesPage";
import "./styles.css";

export function App() {
  return (
    <AppLayout>
      <RepositoriesPage />
    </AppLayout>
  );
}
