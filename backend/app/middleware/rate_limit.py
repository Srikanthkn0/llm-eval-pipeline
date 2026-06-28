import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _limit_for_path(self, path: str) -> int:
        if path.startswith("/api/evals/run"):
            return settings.RATE_LIMIT_EVALS_PER_MIN
        return settings.RATE_LIMIT_PER_MIN

    def _check(self, key: str, limit: int) -> Response | None:
        now = time.time()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Retry in a minute."},
            )
        window.append(now)
        return None

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS" or request.url.path.startswith("/health"):
            return await call_next(request)

        key = f"{self._client_key(request)}:{request.url.path}"
        blocked = self._check(key, self._limit_for_path(request.url.path))
        if blocked is not None:
            return blocked
        return await call_next(request)