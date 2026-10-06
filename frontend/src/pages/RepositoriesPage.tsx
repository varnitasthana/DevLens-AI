import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { RepositoryForm } from "../components/RepositoryForm";
import { RepositoryList } from "../components/RepositoryList";
import {
  createRepository,
  deleteRepository,
  fetchRepositories,
  updateRepository,
} from "../services/api";
import type { Repository, RepositoryInput } from "../types/repository";

type View = "list" | "create" | "detail" | "edit";

export function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selected, setSelected] = useState<Repository | null>(null);
  const [view, setView] = useState<View>("list");
  const [error, setError] = useState<string | null>(null);

  async function loadRepositories() {
    setRepositories(await fetchRepositories());
  }

  useEffect(() => {
    loadRepositories().catch((loadError: unknown) => {
      setError(loadError instanceof Error ? loadError.message : "Unable to load repositories");
    });
  }, []);

  async function handleCreate(data: RepositoryInput) {
    await createRepository(data);
    await loadRepositories();
    setView("list");
  }

  async function handleUpdate(data: RepositoryInput) {
    if (!selected) return;
    await updateRepository(selected.id, data);
    await loadRepositories();
    setSelected((await fetchRepositories()).find((item) => item.id === selected.id) ?? null);
    setView("detail");
  }

  async function handleDelete() {
    if (!selected || !window.confirm(`Delete ${selected.name}?`)) return;
    await deleteRepository(selected.id);
    setSelected(null);
    await loadRepositories();
    setView("list");
  }

  if (view === "create") {
    return <RepositoryForm onSubmit={handleCreate} onCancel={() => setView("list")} />;
  }
  if (view === "edit" && selected) {
    return <RepositoryForm repository={selected} onSubmit={handleUpdate} onCancel={() => setView("detail")} />;
  }
  if (view === "detail" && selected) {
    return (
      <section className="detail-card">
        <button className="button-link" onClick={() => setView("list")}>Back to repositories</button>
        <p className="eyebrow">Repository detail</p>
        <h2>{selected.name}</h2>
        <p>{selected.description || "No description provided."}</p>
        <dl>
          <dt>Source URL</dt><dd>{selected.source_url}</dd>
          <dt>Default branch</dt><dd>{selected.default_branch}</dd>
        </dl>
        <div className="form-actions">
          <Link className="button-link" to={`/repositories/${selected.id}/analysis`}>Analyze repository</Link>
          <button onClick={() => setView("edit")}>Edit repository</button>
          <button className="button-danger" onClick={handleDelete}>Delete repository</button>
        </div>
      </section>
    );
  }

  return (
    <>
      {error && <p className="status status-error">{error}</p>}
      <RepositoryList
        repositories={repositories}
        onCreate={() => setView("create")}
        onSelect={(repository) => { setSelected(repository); setView("detail"); }}
      />
    </>
  );
}
