from typing import Optional, Tuple
import time
import redis
from fastapi import HTTPException, Request
from app.core.config import settings


class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.rate_limits = {
            "default": (60, 100),  # 100 requests per minute
            "auth": (3600, 10),    # 10 requests per hour
            "api": (60, 1000),     # 1000 requests per minute
            "websocket": (60, 100) # 100 connections per minute
        }

    def get_rate_limit(self, endpoint: str) -> Tuple[int, int]:
        """Get rate limit for an endpoint"""
        for key, limit in self.rate_limits.items():
            if key in endpoint:
                return limit
        return self.rate_limits["default"]

    async def is_rate_limited(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> bool:
        """Check if request should be rate limited"""
        # Get client identifier
        client_id = str(user_id) if user_id else request.client.host
        endpoint = request.url.path
        
        # Get rate limit for endpoint
        window, max_requests = self.get_rate_limit(endpoint)
        
        # Create Redis key
        key = f"rate_limit:{endpoint}:{client_id}"
        
        # Get current count
        current = self.redis_client.get(key)
        if current is None:
            # First request in window
            self.redis_client.setex(key, window, 1)
            return False
        
        current = int(current)
        if current >= max_requests:
            return True
        
        # Increment counter
        self.redis_client.incr(key)
        return False

    def get_remaining_requests(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> int:
        """Get remaining requests in current window"""
        client_id = str(user_id) if user_id else request.client.host
        endpoint = request.url.path
        window, max_requests = self.get_rate_limit(endpoint)
        
        key = f"rate_limit:{endpoint}:{client_id}"
        current = self.redis_client.get(key)
        
        if current is None:
            return max_requests
        
        return max(0, max_requests - int(current))

    def get_reset_time(
        self,
        request: Request,
        user_id: Optional[int] = None
    ) -> int:
        """Get time until rate limit resets"""
        client_id = str(user_id) if user_id else request.client.host
        endpoint = request.url.path
        window, _ = self.get_rate_limit(endpoint)
        
        key = f"rate_limit:{endpoint}:{client_id}"
        ttl = self.redis_client.ttl(key)
        
        return max(0, ttl)


# Create a singleton instance
rate_limiter = RateLimiter() 