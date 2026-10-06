import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { useState } from "react";

import { fetchAnalysis, fetchFindings } from "../services/api";

export function FindingsPage() {
  const { analysisId } = useParams();
  const [filters, setFilters] = useState({ severity: "", category: "", source: "", file: "" });
  const analysis = useQuery({ queryKey: ["analysis", analysisId], queryFn: () => fetchAnalysis(analysisId!), enabled: Boolean(analysisId) });
  const findings = useQuery({
    queryKey: ["findings", analysisId, filters],
    queryFn: () => fetchFindings(
      analysisId!,
      Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
    ),
    enabled: Boolean(analysisId),
  });
  if (analysis.isLoading || findings.isLoading) return <p className="status">Loading findings…</p>;
  if (analysis.isError || findings.isError) return <p className="status status-error">Unable to load analysis findings.</p>;
  return (
    <section>
      <Link className="button-link" to={`/repositories/${analysis.data?.repository_id}/analysis`}>Run another analysis</Link>
      <p className="eyebrow">Findings</p>
      <h2>Analysis {analysis.data?.status}</h2>
      <p className="hero-copy">{analysis.data?.files_analyzed} files analyzed in {Math.round(analysis.data?.duration_ms ?? 0)} ms.</p>
      <div className="filter-bar">
        {(["severity", "category", "source", "file"] as const).map((filter) => (
          <input
            key={filter}
            aria-label={filter}
            placeholder={`Filter by ${filter}`}
            value={filters[filter]}
            onChange={(event) => setFilters((current) => ({ ...current, [filter]: event.target.value }))}
          />
        ))}
      </div>
      {findings.data?.length === 0 ? <p className="empty-state">No findings were reported.</p> : (
        <div className="finding-list">
          {findings.data?.map((finding) => (
            <article className="detail-card" key={finding.id}>
              <div className="finding-heading"><strong>{finding.rule}</strong><span>{finding.severity}</span></div>
              <p>{finding.message}</p><small>{finding.file}:{finding.line}:{finding.column} · {finding.source}</small>
              {finding.remediation && <p><strong>Remediation:</strong> {finding.remediation}</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
