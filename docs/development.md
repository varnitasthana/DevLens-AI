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

## Environment

Start from the root `.env.example` and create a local `.env`. Secrets belong
only in local or deployment secret management and must not be committed.
