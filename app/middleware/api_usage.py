from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
from typing import Dict, Optional

from app.core.database import get_db
from app.models.api_key import APIKey
from app.models.api_usage import APIUsage
from app.core.config import settings
from app.core.alerts import AlertService

class APIUsageMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {
            "minute": 100,  # Requests per minute
            "hour": 1000,   # Requests per hour
            "day": 10000    # Requests per day
        }
        self.usage_cache: Dict[str, Dict[str, int]] = {}

    async def dispatch(self, request: Request, call_next):
        # Skip middleware for non-API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key"}
            )

        # Get database session
        db: Session = next(get_db())

        # Verify API key
        api_key_obj = db.query(APIKey).filter(
            APIKey.key == api_key,
            APIKey.is_active == True
        ).first()

        if not api_key_obj:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"}
            )

        # Check rate limits
        current_time = datetime.utcnow()
        rate_limit_exceeded = self._check_rate_limits(api_key, current_time)
        if rate_limit_exceeded:
            return JSONResponse(
                status_code=429,
                content={"detail": rate_limit_exceeded}
            )

        # Start timing the request
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time

            # Log API usage
            self._log_api_usage(
                db,
                api_key_obj.id,
                request.url.path,
                request.method,
                response.status_code,
                response_time
            )

            # Check for alerts
            alert_service = AlertService(db)
            await alert_service.check_all_alerts(
                api_key_obj.id,
                response_time,
                request.url.path
            )

            # Add rate limit headers
            self._add_rate_limit_headers(response, api_key, current_time)

            return response

        except Exception as e:
            # Log error and re-raise
            response_time = time.time() - start_time
            self._log_api_usage(
                db,
                api_key_obj.id,
                request.url.path,
                request.method,
                500,
                response_time
            )
            raise

    def _check_rate_limits(self, api_key: str, current_time: datetime) -> Optional[str]:
        """Check if any rate limits have been exceeded."""
        if api_key not in self.usage_cache:
            self.usage_cache[api_key] = {
                "minute": {"count": 0, "reset": current_time + timedelta(minutes=1)},
                "hour": {"count": 0, "reset": current_time + timedelta(hours=1)},
                "day": {"count": 0, "reset": current_time + timedelta(days=1)}
            }

        for period, limit in self.rate_limits.items():
            cache = self.usage_cache[api_key][period]
            
            # Reset counter if period has elapsed
            if current_time >= cache["reset"]:
                cache["count"] = 0
                cache["reset"] = current_time + timedelta(**{f"{period}s": 1})
            
            # Check if limit exceeded
            if cache["count"] >= limit:
                reset_in = int((cache["reset"] - current_time).total_seconds())
                return f"Rate limit exceeded for {period}. Try again in {reset_in} seconds"
            
            # Increment counter
            cache["count"] += 1

        return None

    def _log_api_usage(
        self,
        db: Session,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float
    ):
        """Log API usage to database."""
        usage = APIUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time
        )
        db.add(usage)
        
        # Update API key usage stats
        api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if api_key:
            api_key.usage_count += 1
            api_key.last_used = datetime.utcnow()
        
        db.commit()

    def _add_rate_limit_headers(self, response: Response, api_key: str, current_time: datetime):
        """Add rate limit headers to response."""
        cache = self.usage_cache.get(api_key, {})
        
        for period in self.rate_limits.keys():
            if period in cache:
                limit = self.rate_limits[period]
                remaining = limit - cache[period]["count"]
                reset_in = int((cache[period]["reset"] - current_time).total_seconds())
                
                response.headers[f"X-RateLimit-{period.capitalize()}-Limit"] = str(limit)
                response.headers[f"X-RateLimit-{period.capitalize()}-Remaining"] = str(remaining)
                response.headers[f"X-RateLimit-{period.capitalize()}-Reset"] = str(reset_in) 