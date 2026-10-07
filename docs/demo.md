# Recruiter Demo Guide

## Availability

There is currently no claimed public demo URL. The workflow below is verified
against the local Docker Compose stack and can be used immediately after a
future deployment has passed the deployment checklist.

## What the demo shows

The deterministic demo path demonstrates:

1. Authentication.
2. Repository ownership.
3. Safe ZIP ingestion.
4. Background analysis through Celery and Redis.
5. Persisted static-analysis findings.
6. Analysis status and dashboard data.
7. Finding filters.

The AI provider and GitHub workflows are optional and require server-side
credentials. They should not be presented as active in a public demo unless
they have been explicitly configured and tested.

## Local demonstration

Start the verified local stack:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:5173
```

Then:

1. Open **Sign in** and choose **Register**.
2. Create a test account using a non-sensitive local email address.
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

```text
http://localhost:8000/docs
```

The health endpoints are public:

```text
http://localhost:8000/api/v1/health
http://localhost:8000/api/v1/health/ready
```

Repository, analysis, findings, dashboard, chat, GitHub, and pull-request
review operations require a bearer token obtained from registration or login.

## What to mention in a portfolio presentation

DevLens is strongest as a demonstration of engineering boundaries and
integration work:

- asynchronous FastAPI routes keep blocking persistence work off the event
  loop;
- Alembic owns the PostgreSQL schema;
- Redis and Celery separate analysis work from the request lifecycle;
- ZIP ingestion validates paths and resource limits before processing;
- static and AI findings use a normalized model with explicit source labels;
- repository ownership is enforced server-side;
- optional AI and GitHub credentials never belong in the frontend.

## Public-demo safety

Before sharing a public URL, verify:

- registration and login work over HTTPS;
- rate limiting is enabled;
- upload and file-count limits are active;
- unauthenticated requests receive HTTP 401;
- another account cannot access the first account's repository;
- no secrets appear in frontend assets, API responses, or logs;
- the demo account and sample data contain no sensitive information.

## Demo limitations

- No public URL is claimed until an external deployment is completed and
  tested end to end.
- Chat, GitHub import, and pull-request review currently exist as backend APIs
  rather than dedicated frontend workflows.
- AI review requires a configured provider and should be described as optional.
- The demo is not a substitute for production load testing or a security
  certification.
