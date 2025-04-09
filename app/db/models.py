from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base
from datetime import datetime

class SeverityLevel(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    severity = Column(Enum(SeverityLevel))
    cvss_score = Column(Float)
    published_date = Column(DateTime)
    last_modified_date = Column(DateTime)
    source = Column(String)  # e.g., "BSI", "NVD", etc.
    references = Column(Text)  # JSON string of references
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Profile Information
    name = Column(String)
    phone = Column(String)
    company = Column(String)
    
    # Preferences
    newsletter_subscribed = Column(Boolean, default=False)
    email_frequency = Column(String, default="weekly")  # daily, weekly, monthly
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")
    activities = relationship("UserActivity", back_populates="user")

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # login, password_change, profile_update, etc.
    details = Column(Text)  # JSON string of activity details
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")

class APIKeyUsage(Base):
    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey("api_keys.id"))
    endpoint = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)

    api_key = relationship("APIKey", back_populates="usage_logs")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    key = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("APIKeyUsage", back_populates="api_key")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    description = Column(Text)
    status = Column(String, default="open")  # open, in_progress, closed
    priority = Column(String, default="medium")  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="tickets")
    responses = relationship("TicketResponse", back_populates="ticket")

class TicketResponse(Base):
    __tablename__ = "ticket_responses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    ticket = relationship("Ticket", back_populates="responses")
    user = relationship("User") 