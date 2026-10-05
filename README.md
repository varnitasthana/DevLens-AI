# DevLens

DevLens is an AI-powered developer productivity platform. Phase 1 establishes
the project foundation and a health-check vertical slice; product analysis
features are intentionally not implemented yet.

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
`http://localhost:8000/api/v1/health`.

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

This starts the backend, frontend, and PostgreSQL development services.

## Project layout

- `backend/app`: FastAPI application code
- `backend/tests`: backend tests
- `frontend/src`: React and TypeScript application code
- `docs`: architecture and development conventions
- `docker-compose.yml`: local development services

## Current scope

Phase 1 provides configuration, service containers, a health endpoint, and
basic frontend/backend validation. Repository analysis, authentication,
background jobs, Redis, and AI integrations are planned for later phases.

