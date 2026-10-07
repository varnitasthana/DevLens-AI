# DevLens

DevLens is a FastAPI and React application for reviewing software repositories.
It combines safe repository ingestion, deterministic static analysis, optional
AI review, persisted findings, background analysis jobs, and repository-aware
chat behind authenticated APIs.

> **Deployment status:** Deployed on Render with CI/CD via GitHub Actions.
> - Live frontend: https://devlens-frontend.onrender.com
> - API: https://devlens-backend.onrender.com
> - OpenAPI: https://devlens-backend.onrender.com/docs
> - Health: https://devlens-backend.onrender.com/api/v1/health
> - Readiness: https://devlens-backend.onrender.com/api/v1/health/ready
> - Managed PostgreSQL, Redis, and Render Object Storage are configured via `render.yaml`.

## Contents

- [What it solves](#what-it-solves)
- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Local setup](#local-setup)
- [Core workflow](#core-workflow)
- [Security](#security)
- [Verification](#verification)
- [Deployment](#deployment)
- [Limitations](#limitations)

## What it solves

Repository review often requires manually combining file discovery, static
analysis, AI feedback, and issue tracking. DevLens provides one workflow for
uploading a repository archive, running analysis, reviewing normalized findings,
and inspecting the result from a browser dashboard.

## Features

- Authenticated users and repository ownership isolation.
- ZIP ingestion with path-traversal, size, file-count, binary-file, and ignored-directory protections.
- Python and JavaScript/TypeScript deterministic analysis.
- Optional provider-neutral AI review with bounded context and validated output.
- Persisted analyses and findings with severity, category, source, and file filters.
- Celery and Redis background analysis with lifecycle states.
- AI-assisted Python test generation returned as review-only text.
- Repository-aware AI chat using bounded keyword retrieval and file citations.
- Server-side GitHub repository metadata import.
- Diff-first pull-request review that does not post comments or modify source.
- React dashboard, repository management, analysis status, and findings views.

## Architecture

```text
React + TypeScript + nginx
            |
            v
FastAPI /api/v1
  |       |        |
  |       |        +--> Auth, ownership, rate limiting, security headers
  |       +-----------> Repository, analysis, findings, dashboard APIs
  +-------------------> PostgreSQL via SQLAlchemy and Alembic

Analysis upload
      |
      v
FastAPI -> Redis -> Celery worker -> ingestion/static/optional AI analysis
                                      |
                                      v
                                  PostgreSQL
```

See [docs/architecture.md](docs/architecture.md) for the detailed component
boundaries and [docs/security.md](docs/security.md) for security assumptions.

## Technology stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, psycopg, Alembic.
- Analysis: Python AST/Ruff-based checks and JavaScript/TypeScript analysis.
- AI: provider abstraction with OpenAI-compatible HTTP behavior and strict
  Pydantic response validation.
- Frontend: React, TypeScript, React Router, React Query, Vite, Tailwind.
- Infrastructure: PostgreSQL, Redis, Celery, Docker Compose, nginx.
- Quality: pytest, Ruff, mypy, Vitest, ESLint, TypeScript.

## Project structure

```text
backend/
  app/
    api/          Versioned FastAPI routes
    analyzers/    Language-specific static analyzers
    ai/           Provider abstraction and response validation
    core/         Settings, auth, errors, middleware, rate limiting
    models/       SQLAlchemy persistence models
    repositories/ Database query helpers
    services/     Application workflows
    workers/      Celery application and analysis tasks
  alembic/        Database migrations
  tests/          Unit, API, integration, analyzer, AI, and security tests
frontend/
  src/
    components/   Reusable UI components
    pages/        Dashboard, auth, repositories, analysis, findings
    services/     Typed API client
    layouts/      Application shell and navigation
docs/             Architecture, development, and security documentation
```

## Local setup

### Prerequisites

- Python 3.12 or a compatible supported Python version.
- Node.js 22 and npm.
- Docker Desktop with Compose, for the complete stack.

### Docker Compose

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The backend image applies Alembic migrations before starting. Services are:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Readiness: http://localhost:8000/api/v1/health/ready

The Compose PostgreSQL port is bound to loopback for local development. If
another local process already owns port 5432, use a local Compose override
without changing the internal `db:5432` connection used by the services.

### Backend without Docker

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Configure `DATABASE_URL`, `REDIS_URL`, and other settings through a local
`.env`. Never commit `.env`; use [.env.example](.env.example) as the template.

### Frontend without Docker

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the running API URL when it differs from the default.

## Core workflow

1. Register or sign in through `/auth`.
2. Create a repository from the Repositories page.
3. Upload a ZIP archive for ingestion or analysis.
4. FastAPI queues analysis through Redis and the Celery worker.
5. The worker persists file metadata, static findings, and optional AI findings.
6. The frontend polls the analysis status and displays findings and filters.

The backend also exposes authenticated APIs for repository chat, GitHub import,
and pull-request review. Those capabilities are not currently surfaced as
frontend pages.

## Security

Authentication uses signed, expiring bearer tokens with scrypt password
hashing. Repository and analysis access is ownership-scoped. ZIP extraction
rejects traversal and resource-exhaustion inputs, and source code is never
executed during ingestion or analysis. SQLAlchemy expressions and Pydantic
validation protect database and API boundaries. Redis-backed rate limiting and
security response headers are enabled through the application middleware.

AI credentials and GitHub credentials are server-side environment settings.
Repository content is treated as untrusted prompt data. Generated tests are
returned as text marked `AI GENERATED — REVIEW BEFORE EXECUTION` and are never
executed automatically.

## Verification

Backend checks, run from `backend`:

```powershell
python -m pytest tests -q
python -m ruff check app tests
python -m mypy app
```

Frontend checks, run from `frontend`:

```powershell
npm test -- --run
npm run lint
npm run typecheck
npm run build
```

Infrastructure validation:

```powershell
docker compose config --quiet
```

The latest local verification recorded 79 backend tests passed with 6 skipped,
4 frontend tests passed, and successful Ruff, mypy, ESLint, TypeScript, Vite
build, and Compose configuration checks.

## Deployment

The repository is containerized for deployment on Render as five cooperating
services: frontend/nginx, FastAPI backend, Celery worker, managed PostgreSQL,
and managed Redis, with Render Object Storage (S3-compatible) for analysis
archives. The `render.yaml` at the repository root defines all services and
resources. The backend image applies Alembic migrations before starting.

To deploy:

1. Create a Render account and connect the GitHub repository.
2. Set the `RENDER_DEPLOY_HOOK_URL` GitHub secret from your Render service
   settings, or deploy directly via the Render dashboard from `render.yaml`.
3. Configure optional secrets through the Render environment: `GITHUB_TOKEN`,
   `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL`.
4. Ensure `CORS_ORIGINS` is set to the deployed frontend origin.

See [docs/deployment.md](docs/deployment.md) for the full deployment guide and
[docs/demo.md](docs/demo.md) for the recruiter walkthrough.

## Limitations

- External AI provider calls require credentials and were not live-verified.
- GitHub API calls require suitable server-side credentials and were not
  externally live-verified.
- Chat retrieval is bounded keyword retrieval, not vector search.
- The frontend does not yet provide chat, GitHub import, or pull-request review
  pages.
- TLS termination, secret rotation, monitoring, and incident response belong
  to the deployment environment.
- No production-scale load benchmark or full browser end-to-end test suite is
  included.
