from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class NotificationConfig(Base):
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # email, webhook, slack, teams
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=False)  # Configuration specific to notification type
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notification_configs")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_config_id = Column(Integer, ForeignKey("notification_configs.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    status = Column(String, nullable=False)  # success, failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    notification_config = relationship("NotificationConfig")
    alert = relationship("Alert") 