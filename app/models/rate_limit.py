from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class RateLimit(Base):
    __tablename__ = "rate_limit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    count = Column(Integer, default=1, nullable=False)
    window_start = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="rate_limits")

    # Indexes
    __table_args__ = (
        Index("ix_rate_limit_user_endpoint", "user_id", "endpoint"),
        Index("ix_rate_limit_window_start", "window_start"),
    )
 