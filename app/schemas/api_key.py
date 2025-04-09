from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class APIKeyBase(BaseModel):
    name: str = Field(..., description="Name of the API key")
    description: Optional[str] = Field(None, description="Description of the API key")
    permissions: Optional[List[str]] = Field(None, description="List of permissions for the API key")
    usage_limits: Optional[Dict[str, int]] = Field(None, description="Usage limits for the API key")

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyUpdate(APIKeyBase):
    is_active: Optional[bool] = Field(None, description="Whether the API key is active")
    expires_at: Optional[datetime] = Field(None, description="Expiration date of the API key")

class APIKeyInDB(APIKeyBase):
    id: int
    key: str
    user_id: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True

class APIKeyUsageBase(BaseModel):
    endpoint: str
    method: str
    status_code: int
    response_time: int
    request_data: Optional[Dict]
    response_data: Optional[Dict]

class APIKeyUsageCreate(APIKeyUsageBase):
    api_key_id: int

class APIKeyUsageInDB(APIKeyUsageBase):
    id: int
    api_key_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class APIKeyUsageStats(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    last_used_at: Optional[datetime]
    daily_usage: Dict[str, int]
    monthly_usage: Dict[str, int] 