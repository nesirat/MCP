from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.rate_limit import RateLimit
from app.schemas.rate_limit import RateLimitConfig


class RateLimitService:
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[Tuple[int, str], Tuple[int, datetime]] = {}

    def check_rate_limit(
        self,
        user_id: int,
        endpoint: str,
        config: RateLimitConfig,
    ) -> None:
        """Check if a request is allowed based on rate limits."""
        cache_key = (user_id, endpoint)
        current_time = datetime.utcnow()

        # Check cache first
        if cache_key in self._cache:
            count, window_start = self._cache[cache_key]
            if current_time - window_start <= timedelta(seconds=config.window):
                if count >= config.limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={
                            "X-RateLimit-Limit": str(config.limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(
                                int((window_start + timedelta(seconds=config.window)).timestamp())
                            ),
                        },
                    )
                self._cache[cache_key] = (count + 1, window_start)
                return

        # Check database
        rate_limit = (
            self.db.query(RateLimit)
            .filter(
                RateLimit.user_id == user_id,
                RateLimit.endpoint == endpoint,
                RateLimit.window_start >= current_time - timedelta(seconds=config.window),
            )
            .first()
        )

        if rate_limit:
            if rate_limit.count >= config.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(config.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(
                            int((rate_limit.window_start + timedelta(seconds=config.window)).timestamp())
                        ),
                    },
                )
            rate_limit.count += 1
        else:
            rate_limit = RateLimit(
                user_id=user_id,
                endpoint=endpoint,
                count=1,
                window_start=current_time,
            )
            self.db.add(rate_limit)

        self.db.commit()

        # Update cache
        self._cache[cache_key] = (rate_limit.count, rate_limit.window_start)

    def cleanup_expired_limits(self) -> None:
        """Clean up expired rate limit records."""
        cutoff_time = datetime.utcnow() - timedelta(days=1)
        self.db.query(RateLimit).filter(RateLimit.window_start < cutoff_time).delete()
        self.db.commit()

        # Clean up cache
        current_time = datetime.utcnow()
        self._cache = {
            k: v for k, v in self._cache.items()
            if current_time - v[1] <= timedelta(days=1)
        } 