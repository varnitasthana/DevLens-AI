import { AppLayout } from "./layouts/AppLayout";
import { HomePage } from "./pages/HomePage";
import "./styles.css";

export function App() {
  return (
    <AppLayout>
      <HomePage />
    </AppLayout>
  );
}
