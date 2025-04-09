from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets
import logging
from app.core.database import Base

logger = logging.getLogger(__name__)

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    usage_limits = Column(JSON, nullable=True)  # {"daily": 1000, "monthly": 30000}
    permissions = Column(JSON, nullable=True)  # ["read", "write", "admin"]
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.key = secrets.token_hex(32)  # Generate a random 64-character hex string
    
    def record_usage(self, endpoint: str, status_code: int, response_time: float):
        """Record API key usage"""
        try:
            from app.models.api_key_usage import APIKeyUsage
            usage = APIKeyUsage(
                api_key_id=self.id,
                endpoint=endpoint,
                status_code=status_code,
                response_time=response_time
            )
            self.usage_count += 1
            self.last_used = datetime.utcnow()
            return usage
        except Exception as e:
            logger.error(f"Error recording API key usage: {str(e)}")
            return None 

class APIKeyUsage(Base):
    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Integer, nullable=False)  # in milliseconds
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs") 