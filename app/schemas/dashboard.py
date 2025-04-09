from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class RecentTicket(BaseModel):
    id: int
    subject: str
    status: str
    created_at: datetime

class APIKeyStats(BaseModel):
    id: int
    name: str
    is_active: bool
    usage_count: int
    last_used: Optional[datetime]

class APIUsageData(BaseModel):
    success_rate: float
    avg_response_time: float

class DashboardStats(BaseModel):
    open_tickets: int
    resolved_tickets: int
    active_api_keys: int
    total_api_calls: int
    api_usage: APIUsageData
    recent_tickets: List[RecentTicket]
    api_keys: List[APIKeyStats] 