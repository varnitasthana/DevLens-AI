import { useState } from "react";

import {
  chatWithRepository,
  generateTest,
  importGitHubRepository,
  reviewPullRequest,
  type ChatResult,
  type GeneratedTest,
  type GitHubImportResult,
  type PullRequestReview,
} from "../services/api";

export function GitHubToolsPage() {
  const [importUrl, setImportUrl] = useState("");
  const [importBranch, setImportBranch] = useState("");
  const [importResult, setImportResult] = useState<GitHubImportResult | null>(null);
  const [pullRequestUrl, setPullRequestUrl] = useState("");
  const [pullRequestResult, setPullRequestResult] = useState<PullRequestReview | null>(null);
  const [repositoryId, setRepositoryId] = useState("");
  const [question, setQuestion] = useState("");
  const [chatResult, setChatResult] = useState<ChatResult | null>(null);
  const [fileName, setFileName] = useState("");
  const [source, setSource] = useState("");
  const [testResult, setTestResult] = useState<GeneratedTest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    setPending(true);
    try {
      await action();
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Request failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <p className="eyebrow">Integrations</p>
      <h1>GitHub tools</h1>
      {error && <p className="status status-error">{error}</p>}

      <div className="tool-grid">
        <form className="repository-form" onSubmit={(event) => {
          event.preventDefault();
          void run(async () => setImportResult(await importGitHubRepository(importUrl, importBranch)));
        }}>
          <h2>Import repository</h2>
          <label>GitHub URL<input type="url" required placeholder="https://github.com/owner/repository" value={importUrl} onChange={(event) => setImportUrl(event.target.value)} /></label>
          <label>Branch<input placeholder="Optional" value={importBranch} onChange={(event) => setImportBranch(event.target.value)} /></label>
          <button disabled={pending}>Import</button>
          {importResult && <p>{importResult.name}: {importResult.file_count} files imported.</p>}
        </form>

        <form className="repository-form" onSubmit={(event) => {
          event.preventDefault();
          void run(async () => setPullRequestResult(await reviewPullRequest(pullRequestUrl)));
        }}>
          <h2>Review pull request</h2>
          <label>Pull request URL<input type="url" required placeholder="https://github.com/owner/repository/pull/1" value={pullRequestUrl} onChange={(event) => setPullRequestUrl(event.target.value)} /></label>
          <button disabled={pending}>Review</button>
          {pullRequestResult && (
            <div>
              <p>{pullRequestResult.summary}</p>
              {pullRequestResult.issues.map((issue, index) => <p key={`${issue.file}-${index}`}><strong>{issue.severity}</strong> {issue.issue}</p>)}
            </div>
          )}
        </form>

        <form className="repository-form" onSubmit={(event) => {
          event.preventDefault();
          void run(async () => setChatResult(await chatWithRepository(repositoryId, question)));
        }}>
          <h2>Repository chat</h2>
          <label>Repository ID<input required value={repositoryId} onChange={(event) => setRepositoryId(event.target.value)} /></label>
          <label>Question<textarea required value={question} onChange={(event) => setQuestion(event.target.value)} /></label>
          <button disabled={pending}>Ask</button>
          {chatResult && <p>{chatResult.answer}</p>}
        </form>

        <form className="repository-form" onSubmit={(event) => {
          event.preventDefault();
          void run(async () => setTestResult(await generateTest(fileName, source)));
        }}>
          <h2>Generate Python tests</h2>
          <label>File name<input required pattern=".+" value={fileName} onChange={(event) => setFileName(event.target.value)} placeholder="module.py" /></label>
          <label>Source code<textarea required value={source} onChange={(event) => setSource(event.target.value)} /></label>
          <button disabled={pending}>Generate</button>
          {testResult && (
            <div>
              <p><strong>{testResult.review_banner}</strong></p>
              <pre><code>{testResult.test_code}</code></pre>
            </div>
          )}
        </form>
      </div>
    </section>
  );
}
