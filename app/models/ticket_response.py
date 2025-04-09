from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class TicketResponse(BaseModel):
    __tablename__ = "ticket_responses"
    
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=False)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="responses")
    user = relationship("User") 