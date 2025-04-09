from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import JSONResponse
from app.core.rate_limiter import rate_limiter
from app.core.security import get_current_user
from fastapi import Depends
from typing import Optional


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if any(path in request.url.path for path in [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]):
            return await call_next(request)

        # Get current user if authenticated
        user_id = None
        try:
            current_user = await get_current_user(request)
            user_id = current_user.id
        except:
            pass

        # Check rate limit
        if await rate_limiter.is_rate_limited(request, user_id):
            remaining = rate_limiter.get_remaining_requests(request, user_id)
            reset_time = rate_limiter.get_reset_time(request, user_id)
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "remaining": remaining,
                    "reset_time": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.get_rate_limit(request.url.path)[1]),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        
        remaining = rate_limiter.get_remaining_requests(request, user_id)
        reset_time = rate_limiter.get_reset_time(request, user_id)
        
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.get_rate_limit(request.url.path)[1])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response 