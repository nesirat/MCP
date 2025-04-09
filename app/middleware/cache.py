from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from app.core.cache import cache
from app.core.config import settings


class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip caching for non-GET requests or if caching is disabled
        if request.method != "GET" or not settings.CACHE_ENABLED:
            return await call_next(request)

        # Check if path should be cached
        if not cache.should_cache(request):
            return await call_next(request)

        # Generate cache key
        cache_key = cache.generate_cache_key(request)

        # Try to get cached response
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )

        # Get response from route handler
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add X-Process-Time header
        response.headers["X-Process-Time"] = str(process_time)

        # Cache the response if it's successful
        if response.status_code == 200:
            cache.set(
                cache_key,
                {
                    "content": response.body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }
            )

        return response 