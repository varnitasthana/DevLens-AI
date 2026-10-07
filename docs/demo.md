# Recruiter Demo Guide

## Availability

The application is live and publicly accessible:

- Frontend: https://devlens-frontend.onrender.com
- API docs: https://devlens-backend.onrender.com/docs
- Health: https://devlens-backend.onrender.com/api/v1/health

## What the demo shows

The deterministic demo path demonstrates:

1. Authentication (registration and login).
2. Repository ownership isolation.
3. Safe ZIP ingestion.
4. Background analysis through Celery and Redis.
5. Persisted static-analysis findings.
6. Analysis status and dashboard data.
7. Finding filters.

The AI provider and GitHub workflows are optional and require server-side
credentials. They should be described as optional in a portfolio presentation
unless they have been explicitly configured and tested.

## Live demonstration

Open:

https://devlens-frontend.onrender.com

Then:

1. Click **Sign in** and choose **Register**.
2. Create a test account using a non-sensitive email address.
3. Open **Repositories**.
4. Create a repository with a name, source URL, and branch.
5. Upload a small safe ZIP archive containing source files.
6. Start analysis.
7. Wait for the status to become `COMPLETED`.
8. Open the findings view.
9. Filter by severity, category, source, or file.
10. Return to the dashboard and review the aggregate counts.
11. Sign out and confirm protected pages require authentication again.

Use a small synthetic repository for demonstrations. Do not upload private
company code, credentials, production configuration, or personal data.

## API smoke test

The API documentation is available at:

https://devlens-backend.onrender.com/docs

The health endpoints are public:

https://devlens-backend.onrender.com/api/v1/health
https://devlens-backend.onrender.com/api/v1/health/ready

Repository, analysis, findings, dashboard, chat, GitHub, and pull-request
review operations require a bearer token obtained from registration or login.

## GitHub import (optional)

If a `GITHUB_TOKEN` is configured on the backend:

```bash
curl -X POST \
  https://devlens-backend.onrender.com/api/v1/github/repositories/import \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/owner/repo"}'
```

## Pull-request review (optional)

```bash
curl -X POST \
  https://devlens-backend.onrender.com/api/v1/pull-requests/review \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/owner/repo/pull/42"}'
```

## What to mention in a portfolio presentation

DevLens is strongest as a demonstration of engineering boundaries and
integration work:

- Asynchronous FastAPI routes keep blocking persistence work off the event loop.
- Alembic owns the PostgreSQL schema.
- Redis and Celery separate analysis work from the request lifecycle.
- Analysis archives are stored in Render Object Storage (S3-compatible), not
  on a shared filesystem.
- ZIP ingestion validates paths and resource limits before processing.
- Static and AI findings use a normalized model with explicit source labels.
- Repository ownership is enforced server-side.
- Optional AI and GitHub credentials never belong in the frontend.
- Deployment is infrastructure-as-code via `render.yaml` with CI/CD on push to
  `main`.

## Public-demo safety

The following have been verified for the live deployment:

- Registration and login work over HTTPS.
- Rate limiting is enabled.
- Upload and file-count limits are active.
- Unauthenticated requests receive HTTP 401.
- Another account cannot access the first account's repository.
- No secrets appear in frontend assets, API responses, or logs.
- AI and GitHub features are enabled only when their server-side credentials
  are deliberately configured.
