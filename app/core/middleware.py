from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.rate_limit import RateLimitService
from app.services.audit import AuditService
from app.core.auth import get_current_user


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        rate_limit_config: dict = None,
    ):
        super().__init__(app)
        self.rate_limit_config = rate_limit_config or {
            "default": {"limit": 100, "window": 60},  # 100 requests per minute
            "auth": {"limit": 10, "window": 60},  # 10 login attempts per minute
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        db = SessionLocal()
        try:
            # Get rate limit config for the endpoint
            endpoint = request.url.path
            config = self.rate_limit_config.get(
                endpoint.split("/")[-1],
                self.rate_limit_config["default"]
            )

            # Initialize services
            rate_limit_service = RateLimitService(db)
            audit_service = AuditService(db)

            # Get user if authenticated
            user = None
            try:
                user = await get_current_user(request, db)
            except:
                pass

            # Check rate limit if user is authenticated
            if user:
                rate_limit_service.check_rate_limit(
                    user_id=user.id,
                    endpoint=endpoint,
                    config=config,
                )

            # Process request
            response = await call_next(request)

            # Log audit event
            audit_service.log(
                action=request.method,
                resource_type="endpoint",
                user_id=user.id if user else None,
                resource_id=None,
                details=f"{request.method} {endpoint}",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            return response

        finally:
            db.close()


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add rate limit headers if they exist
        if hasattr(request.state, "rate_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit["limit"])
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit["remaining"])
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit["reset"])
        
        return response 