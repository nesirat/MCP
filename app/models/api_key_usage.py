from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class APIKeyUsage(BaseModel):
    __tablename__ = "api_key_usage"
    
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs") 