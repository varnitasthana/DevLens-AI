import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RepositoryList } from "./RepositoryList";

describe("RepositoryList", () => {
  it("renders the empty state", () => {
    render(<RepositoryList repositories={[]} onCreate={vi.fn()} onSelect={vi.fn()} />);
    expect(screen.getByText(/no repositories yet/i)).toBeTruthy();
  });

  it("renders real repository metadata", () => {
    render(
      <RepositoryList
        repositories={[{
          id: "repo-1",
          name: "DevLens",
          source_url: "https://github.com/example/devlens",
          default_branch: "main",
          description: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }]}
        onCreate={vi.fn()}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("DevLens")).toBeTruthy();
    expect(screen.getByText("main")).toBeTruthy();
  });
});
