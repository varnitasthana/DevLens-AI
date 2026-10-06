# Development

## Conventions

- Keep backend application code under `backend/app`.
- Keep backend tests under `backend/tests`.
- Keep frontend source under `frontend/src`.
- Read configuration from environment variables; never commit `.env`.
- Keep API routes versioned under `/api/v1`.
- Add tests for externally observable behavior.
- Run formatters, linters, type checks, and builds before opening a change.

## Verification commands

Backend:

```powershell
cd backend
pip install -r requirements\development.txt
pytest
ruff check .
mypy app
```

Frontend:

```powershell
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
```

The dashboard uses the real aggregate endpoint:

```powershell
curl.exe http://localhost:8000/api/v1/dashboard
```

GitHub metadata import uses the server-side `GITHUB_TOKEN` when configured;
tokens are never returned to the frontend:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/github/repositories/import `
  -H "Content-Type: application/json" `
  -d '{"url":"https://github.com/owner/repository","branch":"main"}'
```

Pull request review accepts a diff and returns a report without posting
comments or modifying source code:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/pull-requests/review `
  -H "Content-Type: application/json" `
  -d '{"diff":"+++ b/app.py\n+value = eval(user_input)"}'
```

Docker configuration:

```powershell
docker compose config
```

The backend's readiness check requires PostgreSQL to be reachable. A local
backend-only test run can override the `check_database` dependency, as the
health tests do; the application itself does not open a database connection
until `/api/v1/health/ready` is requested.

For database-backed integration tests, use an isolated PostgreSQL database,
apply migrations, and set `DATABASE_URL` before running pytest:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/devlens_test"
cd backend
python -m alembic upgrade head
python -m pytest tests -q
```

Repository ingestion accepts a ZIP upload:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/repositories/{id}/ingest `
  -F "upload=@repository.zip"
```

The ingestion limits are configured through `MAX_ARCHIVE_SIZE_BYTES`,
`MAX_REPOSITORY_SIZE_BYTES`, `MAX_FILE_SIZE_BYTES`, and `MAX_FILE_COUNT`.

An analysis lifecycle can be started from a ZIP upload:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/repositories/{id}/analyses `
  -F "upload=@repository.zip"
```

The response records `QUEUED`, `RUNNING`, `COMPLETED`, or `FAILED` status,
timestamps, duration, files analyzed, analyzer sources, and findings. Retrieve
the complete result or filter findings:

```powershell
curl.exe http://localhost:8000/api/v1/analyses/{analysis_id}
curl.exe "http://localhost:8000/api/v1/analyses/{analysis_id}/findings?source=static&severity=high"
```

AI provider settings are optional and are read from `AI_BASE_URL`,
`AI_API_KEY`, `AI_MODEL`, and `AI_TIMEOUT_SECONDS`. Normal tests use mocked
providers and do not require credentials.

Python test generation is available only when the AI provider is configured:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/test-generation `
  -H "Content-Type: application/json" `
  -d '{"file_name":"calculator.py","source":"def add(a, b): return a + b"}'
```

Generated output is returned as text with the mandatory
`AI GENERATED — REVIEW BEFORE EXECUTION` banner. DevLens never executes
generated tests automatically.

The frontend provides dashboard, repository, analysis upload, and findings
routes. Run its checks with:

```powershell
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

## Environment

Start from the root `.env.example` and create a local `.env`. Secrets belong
only in local or deployment secret management and must not be committed.
