from pydantic import BaseModel, EmailStr, HttpUrl, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"

class NotificationConfigBase(BaseModel):
    name: str
    type: NotificationType
    enabled: bool = True
    config: Dict[str, Any]

class NotificationConfigCreate(NotificationConfigBase):
    pass

class NotificationConfigUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

class NotificationConfigResponse(NotificationConfigBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NotificationLogResponse(BaseModel):
    id: int
    notification_config_id: int
    alert_id: int
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

# Type-specific config validators
class EmailConfig(BaseModel):
    recipients: list[EmailStr]
    template: Optional[str] = None

class WebhookConfig(BaseModel):
    url: HttpUrl
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    template: Optional[str] = None

class SlackConfig(BaseModel):
    webhook_url: HttpUrl
    channel: str
    username: Optional[str] = None
    icon_emoji: Optional[str] = None

class TeamsConfig(BaseModel):
    webhook_url: HttpUrl
    title: Optional[str] = None
    theme_color: Optional[str] = None 