import type { Repository } from "../types/repository";

type RepositoryListProps = {
  repositories: Repository[];
  onSelect: (repository: Repository) => void;
  onCreate: () => void;
};

export function RepositoryList({ repositories, onSelect, onCreate }: RepositoryListProps) {
  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>Repositories</h2>
        </div>
        <button onClick={onCreate}>Add repository</button>
      </div>
      {repositories.length === 0 ? (
        <p className="empty-state">No repositories yet. Add your first repository.</p>
      ) : (
        <div className="repository-grid">
          {repositories.map((repository) => (
            <button className="repository-card" key={repository.id} onClick={() => onSelect(repository)}>
              <strong>{repository.name}</strong>
              <span>{repository.source_url}</span>
              <small>{repository.default_branch}</small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
