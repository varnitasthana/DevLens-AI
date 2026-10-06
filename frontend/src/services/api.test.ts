import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchRepositories } from "./api";

describe("API service", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parses repository responses from the real API contract", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "repo-1",
            name: "DevLens",
            source_url: "https://github.com/example/devlens",
            default_branch: "main",
            description: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await expect(fetchRepositories()).resolves.toHaveLength(1);
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/repositories",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } }),
    );
  });

  it("surfaces API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: { message: "Unauthorized" } }), { status: 401 }),
    );

    await expect(fetchRepositories()).rejects.toThrow("Unauthorized");
  });
});
