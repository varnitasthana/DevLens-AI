# Deployment Guide

## Deployment status

DevLens is deployed on Render with CI/CD via GitHub Actions. The production
stack is defined as infrastructure-as-code in `render.yaml` at the repository
root.

- Frontend: https://devlens-frontend.onrender.com
- Backend API: https://devlens-backend.onrender.com
- OpenAPI docs: https://devlens-backend.onrender.com/docs
- Health: https://devlens-backend.onrender.com/api/v1/health
- Readiness: https://devlens-backend.onrender.com/api/v1/health/ready

## Render topology

The `render.yaml` blueprint provisions five resources:

```text
HTTPS (Render edge)
       |
       +--> devlens-frontend  (nginx serving built Vite assets)
       |
       +--> devlens-backend  (FastAPI + Uvicorn)
       |            |
       |            +--> devlens-postgres  (managed PostgreSQL)
       |            +--> devlens-redis     (managed Redis)
       |            +--> devlens-storage   (managed Object Storage / S3)
       |
       +--> devlens-worker  (Celery background worker)
                    |
                    +--> devlens-postgres
                    +--> devlens-redis
                    +--> devlens-storage
```

Analysis ZIP archives are uploaded to Render Object Storage via the
`StorageService` abstraction (`app/services/storage.py`). The web service
uploads the archive and passes an opaque storage key to Celery; the worker
downloads the object to a temporary local file, processes it, and cleans up
both the local copy and the storage object. This avoids any reliance on a
shared filesystem between the web service and the worker.

## Required environment variables

Render-managed values are wired automatically through `render.yaml`. Set the
following as Render secrets for the services that need them:

| Variable           | Where      | Source                       |
| ------------------ | ---------- | ---------------------------- |
| `AUTH_SECRET_KEY`  | All        | Render-generated (auto)      |
| `CORS_ORIGINS`     | Backend    | `https://devlens-frontend.onrender.com` |
| `GITHUB_TOKEN`     | Backend    | GitHub Personal Access Token |
| `AI_BASE_URL`      | Backend    | AI provider endpoint         |
| `AI_API_KEY`       | Backend    | AI provider API key          |
| `AI_MODEL`         | Backend    | AI provider model name       |
| `VITE_API_BASE_URL`| Frontend   | `https://devlens-backend.onrender.com` |

AI and GitHub credentials are optional. Without them, the application runs in
deterministic static-analysis mode only.

## Rollout order

1. Merge to `main` — the GitHub Actions workflow runs lint, typecheck, tests,
   and Compose validation.
2. On success, the `deploy-render` job triggers the Render deploy hook.
3. Render builds and deploys the backend, runs Alembic migrations, and marks
   the service healthy once `/api/v1/health/ready` passes.
4. The worker and frontend deploy in parallel, gated on backend health.

## Deployment verification checklist

- [x] HTTPS frontend loads.
- [x] `/api/v1/health` returns HTTP 200.
- [x] `/api/v1/health/ready` reports the database as `ok`.
- [x] Registration and login work.
- [x] Unauthenticated protected requests return HTTP 401.
- [x] A repository can be created.
- [x] A safe ZIP archive can be analyzed.
- [x] Analysis reaches `COMPLETED`.
- [x] Findings are persisted and filterable.
- [x] GitHub import works from a public GitHub URL.
- [x] Pull-request review works via `/api/v1/pull-requests/review`.
- [x] No credentials appear in browser responses or frontend assets.

## Troubleshooting

### Analysis remains queued

Check Redis connectivity, the Celery worker logs, and that the worker uses the
same `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and S3
credentials as the backend.

### Browser requests fail with CORS errors

Set `CORS_ORIGINS` to the exact HTTPS frontend origin, without a trailing path,
and redeploy the backend.

### Direct frontend routes return 404

Confirm that the production image includes `frontend/nginx.conf` and that its
SPA fallback points unknown routes to `/index.html`.

### S3 / Object Storage errors

Verify that `S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`,
`S3_SECRET_ACCESS_KEY`, and `S3_REGION` are set on both the web service and the
worker. The bucket must be reachable from both services.
