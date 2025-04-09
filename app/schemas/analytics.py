from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class APIAnalyticsBase(BaseModel):
    api_id: int
    response_time: float
    status_code: int
    success: int
    error_count: int = 0
    request_count: int = 1


class APIAnalyticsCreate(APIAnalyticsBase):
    pass


class APIAnalyticsResponse(APIAnalyticsBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class APITrendBase(BaseModel):
    api_id: int
    period: int = Field(..., description="Time period in minutes")
    avg_response_time: float
    success_rate: float
    error_rate: float
    request_count: int
    error_count: int


class APITrendCreate(APITrendBase):
    pass


class APITrendResponse(APITrendBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class AnalyticsSummary(BaseModel):
    total_requests: int
    total_errors: int
    avg_response_time: float
    success_rate: float
    error_rate: float
    recent_trends: List[APITrendResponse]


class TimeRange(BaseModel):
    start_time: datetime
    end_time: datetime


class AnalyticsFilter(BaseModel):
    time_range: Optional[TimeRange] = None
    api_id: Optional[int] = None
    period: Optional[int] = None  # in minutes 