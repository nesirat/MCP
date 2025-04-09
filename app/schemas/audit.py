from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    action: str = Field(..., max_length=50)
    resource_type: str = Field(..., max_length=50)
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None 