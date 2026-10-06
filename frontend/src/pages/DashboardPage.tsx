import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchDashboard } from "../services/api";

export function DashboardPage() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  return (
    <section className="dashboard">
      <p className="eyebrow">Overview</p>
      <h1>Code intelligence workspace</h1>
      <p className="hero-copy">Scan repositories, inspect deterministic findings, and review analysis results.</p>
      {dashboard.isLoading && <p className="status">Loading dashboard…</p>}
      {dashboard.isError && <p className="status status-error">{dashboard.error.message}</p>}
      {dashboard.data && (
        <div className="metric-grid">
          <article className="detail-card"><strong>{dashboard.data.repositories}</strong><span>Repositories</span></article>
          <article className="detail-card"><strong>{dashboard.data.total_analyses}</strong><span>Analyses</span></article>
          <article className="detail-card"><strong>{dashboard.data.findings_total}</strong><span>Findings</span></article>
          <article className="detail-card"><strong>{dashboard.data.security_findings}</strong><span>Security findings</span></article>
          <article className="detail-card"><strong>{dashboard.data.latest_analysis_status ?? "—"}</strong><span>Latest status</span></article>
          <article className="detail-card"><strong>{dashboard.data.files_analyzed}</strong><span>Files analyzed</span></article>
        </div>
      )}
      <Link className="button-link" to="/repositories">Manage repositories</Link>
    </section>
  );
}
