from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.types import ASGIApp, Receive, Scope, Send
from uuid import uuid4


class RedisRateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        redis_url: str | None,
        limit: int,
        window_seconds: int,
    ) -> None:
        self.app = app
        self.redis_url = redis_url
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.redis_url:
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        protected_prefixes = ("/api/v1/auth/", "/api/v1/github", "/api/v1/pull-requests", "/api/v1/test-generation")
        expensive = any(path.startswith(prefix) for prefix in protected_prefixes) or path.endswith("/ingest") or path.endswith("/analyses")
        if not expensive:
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        address = client[0] if client else "unknown"
        key = f"devlens:rate:{address}:{path}"
        redis = Redis.from_url(self.redis_url, decode_responses=True)
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.window_seconds)
            if count > self.limit:
                await send({"type": "http.response.start", "status": 429, "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(self.window_seconds).encode()),
                    (b"x-request-id", str(uuid4()).encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"cache-control", b"no-store"),
                ]})
                await send({"type": "http.response.body", "body": b'{"detail":"Rate limit exceeded"}'})
                return
        except RedisError:
            # Availability of the limiter must not take the API offline.
            pass
        finally:
            await redis.aclose()
        await self.app(scope, receive, send)
