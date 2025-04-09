from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertBase(BaseModel):
    type: str
    level: str
    message: str
    value: float
    threshold: float
    api_key_id: int
    user_id: int

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None

class AlertResponse(AlertBase):
    id: int
    status: str
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 