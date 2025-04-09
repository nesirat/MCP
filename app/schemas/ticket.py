from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.MEDIUM

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None

class TicketCommentBase(BaseModel):
    message: str = Field(..., min_length=1)

class TicketCommentCreate(TicketCommentBase):
    pass

class TicketComment(TicketCommentBase):
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True

class Ticket(TicketBase):
    id: int
    user_id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    comments: List[TicketComment] = []

    class Config:
        from_attributes = True

class TicketList(BaseModel):
    tickets: List[Ticket]
    total: int
    page: int
    size: int 