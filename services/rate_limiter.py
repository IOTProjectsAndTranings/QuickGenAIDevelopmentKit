"""
services/rate_limiter.py
────────────────────────
Sliding window rate limiter middleware.

Fixes applied:
  - M1: Dict size capped at MAX_TRACKED_IPS — no unbounded memory growth
"""

import logging
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)

SKIP_PATHS    = {"/health", "/", "/docs", "/openapi.json", "/redoc"}
MAX_TRACKED_IPS = 5000   # M1: evict oldest when exceeded


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Slide the window — purge expired timestamps
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < RATE_LIMIT_WINDOW
        ]

        if len(self._requests[client_ip]) >= RATE_LIMIT_REQUESTS:
            retry_after = max(
                int(RATE_LIMIT_WINDOW - (now - self._requests[client_ip][0])), 1
            )
            logger.warning("Rate limit exceeded for IP %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[client_ip].append(now)

        # M1: evict oldest IPs if dict is too large
        if len(self._requests) > MAX_TRACKED_IPS:
            oldest_ip = min(
                self._requests,
                key=lambda ip: max(self._requests[ip]) if self._requests[ip] else 0
            )
            del self._requests[oldest_ip]

        return await call_next(request)
