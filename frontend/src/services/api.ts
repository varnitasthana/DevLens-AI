import { apiBaseUrl } from "../lib/config";
import type { HealthResponse } from "../types/health";
import type {
  Repository,
  RepositoryInput,
  RepositoryUpdate,
} from "../types/repository";
import type { Analysis, Finding } from "../types/analysis";
import type { Dashboard } from "../types/dashboard";

const authTokenKey = "devlens_access_token";

export function getAuthToken(): string | null {
  return localStorage.getItem(authTokenKey);
}

export function clearAuthToken(): void {
  localStorage.removeItem(authTokenKey);
  window.dispatchEvent(new Event("devlens-auth-changed"));
}

function authHeaders(): HeadersInit {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders(), ...options?.headers },
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

export async function authenticate(
  path: "/api/v1/auth/login" | "/api/v1/auth/register",
  email: string,
  password: string,
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new Error(body?.error?.message ?? `Authentication failed (${response.status})`);
  }
  const result = (await response.json()) as { access_token: string };
  localStorage.setItem(authTokenKey, result.access_token);
  window.dispatchEvent(new Event("devlens-auth-changed"));
}

export const fetchRepositories = () => request<Repository[]>("/api/v1/repositories");
export const fetchDashboard = () => request<Dashboard>("/api/v1/dashboard");

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

export const fetchAnalysis = (id: string) =>
  request<Analysis>(`/api/v1/analyses/${id}`);

export const fetchFindings = (id: string, filters?: Record<string, string>) => {
  const query = new URLSearchParams(filters).toString();
  return request<Finding[]>(`/api/v1/analyses/${id}/findings${query ? `?${query}` : ""}`);
};

export async function createAnalysis(repositoryId: string, file: File): Promise<Analysis> {
  const form = new FormData();
  form.append("upload", file);
  const response = await fetch(`${apiBaseUrl}/api/v1/repositories/${repositoryId}/analyses`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!response.ok) throw new Error(`Analysis request failed (${response.status})`);
  return response.json() as Promise<Analysis>;
}
