from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    limit: int = Field(..., gt=0, description="Maximum number of requests allowed")
    window: int = Field(..., gt=0, description="Time window in seconds")


class RateLimitResponse(BaseModel):
    limit: int
    remaining: int
    reset: int


class RateLimitStatus(BaseModel):
    endpoint: str
    current_count: int
    limit: int
    window_start: str
    window_end: str 