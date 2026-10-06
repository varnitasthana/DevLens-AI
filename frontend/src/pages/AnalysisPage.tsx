import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useState } from "react";

import { createAnalysis, fetchRepository } from "../services/api";

export function AnalysisPage() {
  const { repositoryId } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const repository = useQuery({
    queryKey: ["repository", repositoryId],
    queryFn: () => fetchRepository(repositoryId!),
    enabled: Boolean(repositoryId),
  });
  const analysis = useMutation({
    mutationFn: () => createAnalysis(repositoryId!, file!),
    onSuccess: (result) => navigate(`/analyses/${result.id}/findings`),
  });

  if (repository.isLoading) return <p className="status">Loading repository…</p>;
  if (repository.isError) return <p className="status status-error">{repository.error.message}</p>;
  return (
    <section className="detail-card">
      <Link className="button-link" to="/repositories">Back to repositories</Link>
      <p className="eyebrow">Analysis</p>
      <h2>{repository.data?.name}</h2>
      <p>Upload a ZIP archive to run static analysis and optional configured AI analysis.</p>
      <label>
        Repository ZIP
        <input type="file" accept=".zip,application/zip" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
      </label>
      {analysis.isError && <p className="status status-error">{analysis.error.message}</p>}
      <button disabled={!file || analysis.isPending} onClick={() => analysis.mutate()}>
        {analysis.isPending ? "Analyzing…" : "Start analysis"}
      </button>
    </section>
  );
}
