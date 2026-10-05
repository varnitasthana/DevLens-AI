# Architecture

## Phase 1

DevLens currently has two application services:

```text
Browser -> frontend (Vite/React/TypeScript)
             |
             v
         backend (FastAPI) -> PostgreSQL
```

The frontend calls the backend through `VITE_API_BASE_URL`. The backend reads
runtime configuration from environment variables using a typed Pydantic
settings object. PostgreSQL is included in the development compose file as the
data-store foundation, although Phase 1 does not yet define application
tables.

The only API contract currently implemented is `GET /api/v1/health`.

## Deliberately deferred

Repository analyzers, AI providers, authentication, persistent domain models,
workers, Redis, migrations, and GitHub integrations are not part of Phase 1.

