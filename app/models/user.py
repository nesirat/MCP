from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import logging
from sqlalchemy.sql import func
from .base import BaseModel

logger = logging.getLogger(__name__)

class User(BaseModel):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime, nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")
    
    def verify_password(self, password: str) -> bool:
        """Verify the password against the hashed password"""
        try:
            from app.core.security.passwords import verify_password
            return verify_password(password, self.hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False
    
    def update_last_login(self):
        """Update the last login time and reset failed attempts"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.last_failed_login = None
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
    
    def is_locked(self) -> bool:
        """Check if the account is locked due to too many failed attempts"""
        return self.failed_login_attempts >= 5 and (
            self.last_failed_login and 
            (datetime.utcnow() - self.last_failed_login).total_seconds() < 3600
        ) 