from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum, Boolean
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    api_keys = relationship("APIKey", back_populates="user")

class APIKeyUsage(Base):
    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey("api_keys.id"))
    endpoint = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer)
    response_time = Column(Float)

    api_key = relationship("APIKey", back_populates="usage")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(String, nullable=True)
    key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="api_keys")
    usage = relationship("APIKeyUsage", back_populates="api_key") 