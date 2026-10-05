import { useState } from "react";

import type { Repository, RepositoryInput } from "../types/repository";

type RepositoryFormProps = {
  repository?: Repository;
  onSubmit: (data: RepositoryInput) => Promise<void>;
  onCancel: () => void;
};

export function RepositoryForm({
  repository,
  onSubmit,
  onCancel,
}: RepositoryFormProps) {
  const [form, setForm] = useState<RepositoryInput>({
    name: repository?.name ?? "",
    source_url: repository?.source_url ?? "",
    default_branch: repository?.default_branch ?? "main",
    description: repository?.description ?? "",
  });
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof RepositoryInput, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await onSubmit(form);
    } catch (submitError: unknown) {
      setError(submitError instanceof Error ? submitError.message : "Request failed");
    }
  }

  return (
    <form className="repository-form" onSubmit={submit}>
      <label>
        Name
        <input required value={form.name} onChange={(event) => updateField("name", event.target.value)} />
      </label>
      <label>
        Source URL
        <input required type="url" value={form.source_url} onChange={(event) => updateField("source_url", event.target.value)} />
      </label>
      <label>
        Default branch
        <input required value={form.default_branch} onChange={(event) => updateField("default_branch", event.target.value)} />
      </label>
      <label>
        Description
        <textarea value={form.description} onChange={(event) => updateField("description", event.target.value)} />
      </label>
      {error && <p className="status status-error">{error}</p>}
      <div className="form-actions">
        <button type="submit">{repository ? "Save changes" : "Create repository"}</button>
        <button type="button" className="button-muted" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
