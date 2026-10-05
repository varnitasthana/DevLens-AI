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

The backend exposes versioned health contracts:

- `GET /api/v1/health` reports application health.
- `GET /api/v1/health/ready` performs an asynchronous PostgreSQL `SELECT 1`
  check and reports `503` with a structured error if the dependency is down.

All HTTP errors use the `ErrorResponse` schema and include a request ID. The
request context middleware accepts or generates `X-Request-ID`, returns it on
the response, and emits JSON logs.

## Deliberately deferred

Repository analyzers, AI providers, authentication, persistent domain models,
workers, Redis, migrations, and GitHub integrations are not part of Phase 1.
