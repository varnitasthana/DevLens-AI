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

## Environment

Start from the root `.env.example` and create a local `.env`. Secrets belong
only in local or deployment secret management and must not be committed.
