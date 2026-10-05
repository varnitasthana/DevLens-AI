import { apiBaseUrl } from "../lib/config";
import type { HealthResponse } from "../types/health";
import type {
  Repository,
  RepositoryInput,
  RepositoryUpdate,
} from "../types/repository";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new Error(body?.error?.message ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const fetchRepositories = () => request<Repository[]>("/api/v1/repositories");

export const fetchRepository = (id: string) =>
  request<Repository>(`/api/v1/repositories/${id}`);

export const createRepository = (data: RepositoryInput) =>
  request<Repository>("/api/v1/repositories", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateRepository = (id: string, data: RepositoryUpdate) =>
  request<Repository>(`/api/v1/repositories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteRepository = (id: string) =>
  request<void>(`/api/v1/repositories/${id}`, { method: "DELETE" });
