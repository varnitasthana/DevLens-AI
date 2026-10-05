export type Repository = {
  id: string;
  name: string;
  source_url: string;
  default_branch: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type RepositoryInput = {
  name: string;
  source_url: string;
  default_branch: string;
  description: string;
};

export type RepositoryUpdate = Partial<RepositoryInput>;
