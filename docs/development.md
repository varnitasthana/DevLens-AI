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

## Environment

Start from the root `.env.example` and create a local `.env`. Secrets belong
only in local or deployment secret management and must not be committed.

