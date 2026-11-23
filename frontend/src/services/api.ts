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
const demoRepositoryKey = "devlens_demo_repositories";
const demoAnalysisKey = "devlens_demo_analyses";

export function isDemoDeployment(): boolean {
  return typeof window !== "undefined"
    && window.location.hostname === "varnitasthana.github.io";
}

function demoRepositories(): Repository[] {
  const stored = localStorage.getItem(demoRepositoryKey);
  if (stored) {
    try {
      return JSON.parse(stored) as Repository[];
    } catch {
      localStorage.removeItem(demoRepositoryKey);
    }
  }
  const now = "2026-11-23T18:00:00.000Z";
  const repositories: Repository[] = [
    {
      id: "demo-devlens",
      name: "DevLens-AI",
      source_url: "https://github.com/varnitasthana/DevLens-AI",
      default_branch: "main",
      description: "AI-powered repository review platform.",
      created_at: now,
      updated_at: now,
    },
  ];
  localStorage.setItem(demoRepositoryKey, JSON.stringify(repositories));
  return repositories;
}

function saveDemoRepositories(repositories: Repository[]): void {
  localStorage.setItem(demoRepositoryKey, JSON.stringify(repositories));
}

function demoId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function demoFindings(id: string): Finding[] {
  const common = {
    id: `${id}-finding`,
    file: "backend/app/services/analysis.py",
    line: 99,
    column: 12,
    evidence: "Broad exception handling should preserve error context.",
  };
  return [
    { ...common, id: `${id}-1`, rule: "security.dynamic-execution", category: "security", severity: "high", message: "Dynamic execution was not found in the repository review.", source: "static", remediation: "Continue using explicit dispatch rather than eval or exec." },
    { ...common, id: `${id}-2`, file: "frontend/src/services/api.ts", line: 24, rule: "maintainability.api-errors", category: "maintainability", severity: "medium", message: "API errors include the server message and HTTP context.", source: "static", remediation: "Preserve the centralized error response contract." },
    { ...common, id: `${id}-3`, file: "backend/app/core/rate_limit.py", line: 52, rule: "security.rate-limit-failure", category: "security", severity: "low", message: "Redis unavailability is handled with fail-open behavior.", source: "ai", remediation: "Monitor Redis and alert on repeated backend bypasses." },
  ];
}

function demoAnalysis(id: string, repositoryId = "demo-devlens", status = "COMPLETED"): Analysis {
  const now = new Date().toISOString();
  return {
    id,
    repository_id: repositoryId,
    status,
    created_at: now,
    updated_at: now,
    started_at: status === "QUEUED" ? null : now,
    completed_at: status === "COMPLETED" ? now : null,
    duration_ms: status === "COMPLETED" ? 1842 : null,
    files_analyzed: status === "COMPLETED" ? 47 : 0,
    analyzer_source: "static,ai",
    findings: status === "COMPLETED" ? demoFindings(id) : [],
  };
}

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
  if (isDemoDeployment()) {
    return { status: "ok", version: "0.1.0", environment: "github-pages-demo" };
  }
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
  if (isDemoDeployment()) {
    localStorage.setItem(authTokenKey, `demo-token-${demoId("account")}`);
    window.dispatchEvent(new Event("devlens-auth-changed"));
    return;
  }
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

export const fetchRepositories = () =>
  isDemoDeployment()
    ? Promise.resolve(demoRepositories())
    : request<Repository[]>("/api/v1/repositories");
export const fetchDashboard = () =>
  isDemoDeployment()
    ? Promise.resolve({
        repositories: demoRepositories().length,
        total_analyses: 3,
        latest_analysis_id: "demo-analysis",
        latest_analysis_status: "COMPLETED",
        latest_analysis_at: "2026-11-23T18:00:00.000Z",
        findings_total: 8,
        findings_by_severity: { low: 3, medium: 3, high: 2 },
        findings_by_source: { static: 6, ai: 2 },
        security_findings: 2,
        files_analyzed: 47,
      } satisfies Dashboard)
    : request<Dashboard>("/api/v1/dashboard");

export const fetchRepository = (id: string) =>
  isDemoDeployment()
    ? Promise.resolve(demoRepositories().find((item) => item.id === id)!)
    : request<Repository>(`/api/v1/repositories/${id}`);

export const createRepository = (data: RepositoryInput) => {
  if (isDemoDeployment()) {
    const now = new Date().toISOString();
    const repository: Repository = { id: demoId("repo"), ...data, created_at: now, updated_at: now };
    saveDemoRepositories([...demoRepositories(), repository]);
    return Promise.resolve(repository);
  }
  return request<Repository>("/api/v1/repositories", { method: "POST", body: JSON.stringify(data) });
};

export const updateRepository = (id: string, data: RepositoryUpdate) => {
  if (isDemoDeployment()) {
    const updated = demoRepositories().map((item) =>
      item.id === id ? { ...item, ...data, updated_at: new Date().toISOString() } : item,
    );
    saveDemoRepositories(updated);
    return Promise.resolve(updated.find((item) => item.id === id)!);
  }
  return request<Repository>(`/api/v1/repositories/${id}`, { method: "PATCH", body: JSON.stringify(data) });
};

export const deleteRepository = (id: string) => {
  if (isDemoDeployment()) {
    saveDemoRepositories(demoRepositories().filter((item) => item.id !== id));
    return Promise.resolve();
  }
  return request<void>(`/api/v1/repositories/${id}`, { method: "DELETE" });
};

export const fetchAnalysis = (id: string) =>
  isDemoDeployment()
    ? Promise.resolve(demoAnalysis(id))
    : request<Analysis>(`/api/v1/analyses/${id}`);

export const fetchFindings = (id: string, filters?: Record<string, string>) => {
  if (isDemoDeployment()) {
    const findings = demoFindings(id);
    return Promise.resolve(findings.filter((finding) =>
      Object.entries(filters ?? {}).every(([key, value]) =>
        String(finding[key as keyof Finding]).toLowerCase().includes(value.toLowerCase()),
      ),
    ));
  }
  const query = new URLSearchParams(filters).toString();
  return request<Finding[]>(`/api/v1/analyses/${id}/findings${query ? `?${query}` : ""}`);
};

export async function createAnalysis(repositoryId: string, file: File): Promise<Analysis> {
  if (isDemoDeployment()) {
    const analysis = demoAnalysis(demoId("analysis"), repositoryId, "COMPLETED");
    localStorage.setItem(demoAnalysisKey, JSON.stringify(analysis));
    void file;
    return analysis;
  }
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

export type GitHubImportResult = {
  id: string;
  name: string;
  source_url: string;
  default_branch: string;
  file_count: number;
  status: string;
};

export type ChatCitation = {
  file: string;
  line_start: number;
  line_end: number;
};

export type ChatResult = {
  answer: string;
  citations: ChatCitation[];
};

export type PullRequestIssue = {
  file: string;
  severity: string;
  issue: string;
  suggested_fix: string;
  source: string;
};

export type PullRequestReview = {
  summary: string;
  issues: PullRequestIssue[];
  testing_recommendations: string[];
};

export type GeneratedTest = {
  review_banner: string;
  file_name: string;
  test_code: string;
  scenarios: string[];
};

export const importGitHubRepository = (url: string, branch?: string) =>
  isDemoDeployment()
    ? Promise.resolve({
        id: "demo-import",
        name: url.split("/").slice(-2).join("/") || "owner/repository",
        source_url: url,
        default_branch: branch || "main",
        file_count: 47,
        status: "imported",
      })
    : request<GitHubImportResult>("/api/v1/github/repositories/import", {
        method: "POST",
        body: JSON.stringify({ url, branch: branch || null }),
      });

export const chatWithRepository = (repositoryId: string, question: string) =>
  isDemoDeployment()
    ? Promise.resolve({
        answer: `Demo analysis of repository ${repositoryId}: ${question.trim()} DevLens uses static analyzers and bounded repository context to produce review findings.`,
        citations: [{ file: "README.md", line_start: 1, line_end: 24 }],
      })
    : request<ChatResult>(`/api/v1/repositories/${repositoryId}/chat`, {
        method: "POST",
        body: JSON.stringify({ question }),
      });

export const reviewPullRequest = (githubUrl: string) =>
  isDemoDeployment()
    ? Promise.resolve({
        summary: `Demo review completed for ${githubUrl}. No unsafe dynamic execution or direct HTML injection was detected in the sample diff.`,
        issues: [],
        testing_recommendations: [
          "Add or update tests for each changed behavior.",
          "Run the full backend and frontend suites.",
        ],
      })
    : request<PullRequestReview>("/api/v1/pull-requests/review", {
        method: "POST",
        body: JSON.stringify({ github_url: githubUrl }),
      });

export const generateTest = (fileName: string, source: string) =>
  isDemoDeployment()
    ? Promise.resolve({
        review_banner: "AI GENERATED - REVIEW BEFORE EXECUTION",
        file_name: fileName.replace(/\.py$/, "") + "_test.py",
        test_code: `import pytest\n\n\ndef test_generated_scenario():\n    # Review and replace this scaffold with behavior-specific assertions.\n    assert True\n`,
        scenarios: ["Verify the primary behavior", "Verify invalid input handling", "Verify edge cases"],
      })
    : request<GeneratedTest>("/api/v1/test-generation", {
        method: "POST",
        body: JSON.stringify({ file_name: fileName, source }),
      });
