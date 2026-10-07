# Deployment Guide

## Deployment status

DevLens has been verified locally as a Docker Compose application. A public
deployment has not been performed because no external hosting account,
deployment credentials, domain, or managed-service credentials are available
in this repository context.

The repository now includes [render.yaml](../render.yaml), a Render Blueprint
for the fastest safe demo path. It is deployment configuration, not a claim
that the application is currently hosted online.

## Render launch profile

The initial Render profile uses:

- Render PostgreSQL.
- Render Key Value for Redis-compatible rate limiting and Celery transport.
- A FastAPI web service.
- A React/nginx web service.
- `CELERY_TASK_ALWAYS_EAGER=true`.

Eager mode executes the existing Celery analysis task in the API process. This
avoids the separate-worker/shared-filesystem problem for a small demonstration
and keeps the current analysis behavior. It is intentionally not the scalable
background-processing profile: long analyses occupy a web request, and
`/tmp/devlens/uploads` is ephemeral. Keep uploads small and use this profile
only for a portfolio demo.

Render account setup is still required:

1. Create or sign in to a Render account.
2. Connect the `varnitasthana/DevLens-AI` GitHub repository.
3. Create a Blueprint from `render.yaml`.
4. Set `CORS_ORIGINS` to the final frontend HTTPS URL.
5. After the backend service receives its public URL, set
   `VITE_API_BASE_URL` on the frontend service to that backend URL and deploy
   the frontend again.
6. Set `RENDER_DEPLOY_HOOK_URL` as a GitHub Actions repository secret if
   automatic deployment from `main` is desired.

Do not place any database password, Redis credential, AI key, GitHub token, or
authentication secret in GitHub. Render-managed values and generated secrets
must remain in Render's environment/secrets interface.

## Production topology

Deploy the existing architecture as five services:

```text
HTTPS reverse proxy
        |
        +--> frontend/nginx
        |
        +--> FastAPI backend -----> PostgreSQL
                         |
                         +--------> Redis <----- Celery worker
```

The hosting provider must support:

- Docker-based web services.
- A persistent PostgreSQL database.
- A Redis-compatible service reachable by the backend and worker.
- Independent environment variables or secrets for each service.
- HTTPS and a stable frontend hostname.
- Persistent database storage and health checks.

The `render.yaml` launch profile intentionally omits the separate Celery
worker while eager mode is enabled. Do not describe that profile as
asynchronous background processing.

## Required services

### PostgreSQL

Create a persistent PostgreSQL database and provide its connection string as
`DATABASE_URL`. Apply migrations from the backend image before serving traffic:

```powershell
cd backend
python -m alembic upgrade head
```

The current migration head can be checked with:

```powershell
python -m alembic heads
```

Never modify the production schema manually; use Alembic migrations.

### Redis

Create a private Redis service and set:

```text
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

The backend uses Redis for rate limiting and Celery uses it for task transport
and results.

### Backend

Build from `backend/Dockerfile`. The image:

1. Installs runtime dependencies.
2. Includes the application and Alembic files.
3. Runs `alembic upgrade head`.
4. Starts Uvicorn on port `8000`.

Expose only the platform's internal service URL to the frontend configuration
and reverse proxy. The backend health endpoint is:

```text
/api/v1/health
```

The readiness endpoint verifies database connectivity:

```text
/api/v1/health/ready
```

### Celery worker

Build from the same `backend/Dockerfile` and run:

```text
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

The worker must receive the same database, Redis, and upload-directory
configuration as the backend. Use a shared durable location for
`ANALYSIS_UPLOAD_DIR` when the platform does not guarantee a shared filesystem.

The worker is not part of the initial eager-mode Render profile.

### Frontend

Build from `frontend/Dockerfile`. Set the build-time value:

```text
VITE_API_BASE_URL=https://api.example.com
```

Replace the example with the actual HTTPS backend origin. The image serves the
Vite build through nginx and includes SPA history fallback for direct route
navigation.

## Environment configuration

Start with [.env.example](../.env.example), but provide values through the
hosting provider's secret/environment configuration rather than committing a
`.env` file.

Required production settings include:

```text
APP_ENV=production
DATABASE_URL=<managed PostgreSQL URL>
REDIS_URL=<private Redis URL>
CELERY_BROKER_URL=<private Redis URL>
CELERY_RESULT_BACKEND=<private Redis URL>
AUTH_SECRET_KEY=<long random secret>
CORS_ORIGINS=https://<frontend-domain>
```

Optional settings:

```text
AI_BASE_URL=<provider endpoint>
AI_API_KEY=<server-side provider key>
AI_MODEL=<provider model>
GITHUB_TOKEN=<server-side GitHub token>
```

AI and GitHub credentials are not required for the deterministic analysis
demo. Never expose them through frontend variables, browser storage, source
control, logs, or API responses.

Production settings reject the development authentication secret, development
database credentials, and missing Redis configuration.

## Health checks and rollout order

1. Provision PostgreSQL and Redis.
2. Configure backend and worker secrets.
3. Start the backend and wait for `/api/v1/health/ready`.
4. Confirm the migration head.
5. Start the Celery worker and verify its worker ping.
6. Build and serve the frontend with the production API origin.
7. Restrict CORS to the real frontend origin.
8. Terminate HTTPS at the provider or a trusted reverse proxy.
9. Run the smoke test in [demo.md](demo.md).

Do not route public traffic to the frontend until the backend readiness check,
worker, and database migration have succeeded.

## Deployment verification checklist

- [ ] HTTPS frontend loads.
- [ ] `/api/v1/health` returns HTTP 200.
- [ ] `/api/v1/health/ready` reports the database as `ok`.
- [ ] Registration and login work.
- [ ] Unauthenticated protected requests return HTTP 401.
- [ ] A repository can be created.
- [ ] A safe ZIP archive can be analyzed.
- [ ] Analysis reaches `COMPLETED`.
- [ ] Findings are persisted and filterable.
- [ ] Cross-user repository access is denied.
- [ ] No credentials appear in browser responses or frontend assets.
- [ ] AI and GitHub features are enabled only when their server-side
      credentials are deliberately configured.

## Troubleshooting

### Migration failure

Check `DATABASE_URL`, database readiness, and the backend startup logs. Run
`python -m alembic heads` from the backend environment and compare it with the
database's current revision.

### Analysis remains queued

Check Redis connectivity, the Celery worker logs, shared upload storage, and
that the worker uses the same `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and
`DATABASE_URL` as the backend.

### Browser requests fail with CORS errors

Set `CORS_ORIGINS` to the exact HTTPS frontend origin, without a trailing path,
and redeploy the backend.

### Direct frontend routes return 404

Confirm that the production image includes `frontend/nginx.conf` and that its
SPA fallback points unknown routes to `/index.html`.

## Current limitation

The local Compose deployment is verified. A live provider deployment, public
domain, HTTPS certificate, managed database, managed Redis instance, and
external credentialed integrations remain unverified until an owner supplies
hosting access.

## Upgrade path: Render Object Storage

After the demo is live, move analysis archives from the web container's
ephemeral filesystem to Render Object Storage or another S3-compatible object
store. The production upgrade should:

1. Upload the archive to a private object-storage key.
2. Pass an opaque object key, not a local path, to the task.
3. Let the worker download the object to a temporary private file.
4. Run the existing safe ingestion and analysis flow.
5. Delete the temporary file and object after completion or failure.
6. Re-enable `CELERY_TASK_ALWAYS_EAGER=false`.
7. Add a separate Render background worker using the existing Celery command.
8. Verify `QUEUED -> RUNNING -> COMPLETED` with the worker before exposing it
   as the default production profile.

Object Storage is the correct long-term design for independent web and worker
services. It is deliberately not enabled by `render.yaml` yet because the
current code has no object-storage client or bucket lifecycle implementation;
claiming that it was wired would be misleading.
