from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import timedelta

from app.core.cache import CacheService


class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        cache_service: CacheService,
        default_ttl: timedelta = timedelta(minutes=5),
        excluded_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.cache_service = cache_service
        self.default_ttl = default_ttl
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip caching for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip caching for non-GET requests
        if request.method != "GET":
            return await call_next(request)

        # Generate cache key
        cache_key = f"response:{request.url.path}:{request.url.query}"

        # Try to get cached response
        cached_response = await self.cache_service.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )

        # Get fresh response
        response = await call_next(request)

        # Cache the response if it's successful
        if response.status_code == 200:
            await self.cache_service.set(
                cache_key,
                {
                    "content": response.body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                },
                self.default_ttl
            )

        return response 