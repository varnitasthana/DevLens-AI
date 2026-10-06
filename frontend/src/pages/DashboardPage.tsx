import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchRepositories } from "../services/api";

export function DashboardPage() {
  const repositories = useQuery({ queryKey: ["repositories"], queryFn: fetchRepositories });
  return (
    <section className="dashboard">
      <p className="eyebrow">Overview</p>
      <h1>Code intelligence workspace</h1>
      <p className="hero-copy">Scan repositories, inspect deterministic findings, and review analysis results.</p>
      {repositories.isLoading && <p className="status">Loading dashboard…</p>}
      {repositories.isError && <p className="status status-error">{repositories.error.message}</p>}
      {repositories.data && (
        <div className="metric-grid">
          <article className="detail-card"><strong>{repositories.data.length}</strong><span>Repositories</span></article>
          <article className="detail-card"><strong>Ready</strong><span>Analysis service</span></article>
        </div>
      )}
      <Link className="button-link" to="/repositories">Manage repositories</Link>
    </section>
  );
}
