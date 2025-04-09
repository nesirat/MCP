from typing import Any, Optional
from datetime import timedelta
import json
from redis import Redis
from redis.exceptions import RedisError
import redis
from fastapi import Request

from app.core.config import settings


class CacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = timedelta(hours=1)

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError:
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            return self.redis.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(value)
            )
        except RedisError:
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            return bool(self.redis.delete(key))
        except RedisError:
            return False

    async def clear(self) -> bool:
        """Clear all cached values."""
        try:
            return self.redis.flushdb()
        except RedisError:
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except RedisError:
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        try:
            return self.redis.incrby(key, amount)
        except RedisError:
            return None

    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a counter in cache."""
        try:
            return self.redis.decrby(key, amount)
        except RedisError:
            return None

    async def get_or_set(
        self,
        key: str,
        value_func: callable,
        ttl: Optional[timedelta] = None
    ) -> Any:
        """Get a value from cache or set it if not exists."""
        value = await self.get(key)
        if value is None:
            value = await value_func()
            await self.set(key, value, ttl)
        return value


class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not settings.CACHE_ENABLED:
            return None
        
        value = self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not settings.CACHE_ENABLED:
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            ttl = ttl or settings.CACHE_TTL
            return self.redis_client.setex(key, ttl, value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not settings.CACHE_ENABLED:
            return False
        
        return bool(self.redis_client.delete(key))

    def clear(self) -> bool:
        """Clear all cache"""
        if not settings.CACHE_ENABLED:
            return False
        
        return bool(self.redis_client.flushdb())

    def generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        path = request.url.path
        query_params = str(sorted(request.query_params.items()))
        return f"{path}:{query_params}"

    def should_cache(self, request: Request) -> bool:
        """Check if request should be cached"""
        if not settings.CACHE_ENABLED:
            return False
        
        path = request.url.path
        return path not in settings.CACHE_EXCLUDED_PATHS


# Create a singleton instance
cache = RedisCache() 