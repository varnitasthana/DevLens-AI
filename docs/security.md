# Security posture

## Implemented protections

- Bearer authentication with scrypt password hashes and signed expiring tokens.
- Repository ownership checks for repository and analysis data.
- Server-side GitHub and AI credentials; secrets are not returned to clients.
- ZIP traversal, archive, repository, file-count, and file-size protections.
- Ignored repository directories are excluded from analysis.
- SQLAlchemy expression-based database access.
- Strict Pydantic validation for AI responses and generated-test output.
- Generated tests are returned as untrusted text and are never executed.
- Fixed GitHub API host; user input cannot choose an outbound host.
- `nosniff`, `DENY`, `no-referrer`, CSP, and `no-store` response headers.
- PostgreSQL is bound to localhost in the development Compose configuration.

## Deployment assumptions

TLS must terminate at a trusted reverse proxy in production. Local development
continues to use HTTP. The application does not claim to provide end-to-end
TLS itself.

Production deployments must configure `AUTH_SECRET_KEY`, database credentials,
and any provider tokens through a secret manager or deployment environment.
The development defaults are rejected by settings validation outside
development and test environments.

## Residual risks and limitations

- The current authentication foundation is a bearer-token system; refresh-token
  rotation, MFA, OAuth, and account recovery are not implemented.
- Expensive endpoint rate limiting uses Redis when `REDIS_URL` is configured.
  Development without Redis bypasses this middleware; production settings
  reject a missing Redis URL. Redis availability and eviction policy remain
  deployment responsibilities.
- Repository and AI content remains untrusted input. Prompt-injection defenses
  establish an instruction/data boundary but cannot guarantee that an LLM will
  ignore every adversarial string.
- GitHub import and PR review use server-side credentials and must remain behind
  authenticated, authorized routes.
- TLS, network policy, secret rotation, monitoring, and incident response remain
  deployment responsibilities.
