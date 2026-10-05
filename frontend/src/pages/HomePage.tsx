import { HealthStatus } from "../components/HealthStatus";
import { useHealth } from "../hooks/useHealth";

export function HomePage() {
  const { health, error } = useHealth();

  return (
    <section className="hero">
      <p className="eyebrow">Phase 1 foundation</p>
      <h1>Understand your codebase with confidence.</h1>
      <p className="hero-copy">
        DevLens will bring code analysis, actionable explanations, and better
        tests into one developer workflow.
      </p>
      <HealthStatus health={health} error={error} />
    </section>
  );
}
