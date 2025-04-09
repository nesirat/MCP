from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # response_time, error_rate, usage_spike, unauthorized_access
    level = Column(String, nullable=False)  # warning, critical
    message = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    
    # Related entities
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    api_key = relationship("APIKey", back_populates="alerts")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="alerts")
    
    # Status tracking
    status = Column(String, default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 