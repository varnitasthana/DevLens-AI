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

## Persistence

Phase 3 currently persists repository metadata in `repositories`. It includes
a UUID primary key, unique source URL, name and branch metadata, description,
UTC timestamps, and an index for lookup by name. SQLAlchemy 2.x sessions use
the synchronous psycopg driver, and API handlers run database operations via
`asyncio.to_thread` so blocking database calls do not block the event loop.
Alembic owns the schema migration.

Repository files, analyses, findings, and users are intentionally deferred
until their workflows and ownership rules are defined.

## Remaining deferred work

Repository analyzers, AI providers, authentication, workers, Redis, and GitHub
integrations are not part of Phase 3.
