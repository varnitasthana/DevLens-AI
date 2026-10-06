# DevLens

DevLens is an AI-powered developer productivity platform for repository
analysis, findings review, background analysis jobs, and repository-aware AI
chat.

## Quick start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with health at
`http://localhost:8000/api/v1/health`. Authenticated application endpoints
require a bearer token obtained from the auth API.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

### Docker

Copy `.env.example` to `.env`, then run:

```powershell
docker compose up --build
```

This starts the backend, frontend, PostgreSQL, Redis, and Celery worker
development services.

## Project layout

- `backend/app`: FastAPI application code
- `backend/tests`: backend tests
- `frontend/src`: React and TypeScript application code
- `docs`: architecture and development conventions
- `docker-compose.yml`: local development services

## Current scope

The application supports authenticated repository management, safe ZIP
ingestion, static and optional AI analysis, persisted findings, Celery-backed
analysis jobs, dashboard data, GitHub metadata and diff review workflows, and
bounded repository-aware AI chat. See [docs/architecture.md](docs/architecture.md)
and [docs/security.md](docs/security.md) for implemented boundaries and
remaining limitations.
