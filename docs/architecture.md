# Architecture

## System boundary

DevLens is a browser application backed by a versioned FastAPI API. PostgreSQL
stores users, repositories, repository files, analyses, and findings. Redis
supports rate limiting and Celery job transport. A Celery worker performs
analysis outside the request process.

```text
Browser
  |
  v
React/TypeScript frontend served by nginx
  |
  v
FastAPI /api/v1
  |                 \
  v                  v
PostgreSQL       Redis
  ^                  |
  |                  v
  +------------ Celery worker
                       |
                       v
                 analysis services
```

Docker Compose provides the local PostgreSQL, Redis, backend, worker, and
frontend services. The backend image runs `alembic upgrade head` before
starting Uvicorn. The frontend nginx configuration provides SPA history
fallback for direct React route navigation.

## Backend layers

- `app/api/v1`: authenticated HTTP routes and request/response contracts.
- `app/core`: settings, bearer authentication, ownership dependencies,
  structured errors, request context, security headers, and rate limiting.
- `app/models`: SQLAlchemy entities and relationships.
- `app/repositories`: persistence queries.
- `app/services`: repository, ingestion, analysis, dashboard, AI chat, GitHub,
  and pull-request workflows.
- `app/analyzers`: normalized Python and JavaScript/TypeScript static findings.
- `app/ai`: provider abstraction, context selection, prompts, and validated
  AI responses.
- `app/workers`: Celery application and background analysis tasks.

Blocking SQLAlchemy sessions and file work are moved to worker threads from
async route handlers where required. Uploaded source is treated as data and
is not executed.

## Persistence and migrations

Alembic migrations create and evolve:

- users and authentication ownership fields;
- repositories;
- repository file metadata and bounded source content;
- analyses and lifecycle fields;
- normalized analysis findings.

The current migration head is `20261006_0006`. Repository and analysis
queries are scoped to the authenticated owner.

## API capabilities

Implemented backend routes include:

- health and readiness;
- registration and login;
- repository CRUD, ZIP ingestion, and analysis upload;
- analysis status and filtered findings;
- dashboard aggregates;
- Python AI test generation;
- repository-aware chat;
- GitHub repository metadata import;
- diff or GitHub URL pull-request review.

Pull-request review returns a report and does not post comments or modify
source code. GitHub and AI credentials remain server-side.

## Frontend boundary

The frontend currently includes routes for authentication, dashboard,
repository management, analysis upload/status, and findings. It uses React
Query and a typed API client with bearer-token injection. Loading, error, and
empty states are represented in the application pages.

Chat, GitHub import, and pull-request review are implemented as backend APIs
but are not currently surfaced as frontend pages.

## Analysis lifecycle

```text
Upload
  -> QUEUED
  -> RUNNING
  -> COMPLETED or FAILED
```

The worker safely extracts the archive, discovers supported text files,
persists file metadata, runs deterministic analyzers, optionally calls the
configured AI provider with bounded context, and persists normalized findings.
The frontend polls the analysis resource while it is active.

## Trust boundaries

- Authentication tokens are accepted only through the bearer authorization
  header.
- Repository ownership is enforced before repository, analysis, finding, and
  chat access.
- Archive paths and resource limits are validated before extraction.
- AI responses are parsed into application schemas before persistence.
- Repository content is explicitly untrusted context, not executable
  instructions.
- Generated test output is returned as review-only text and is never executed
  automatically.
