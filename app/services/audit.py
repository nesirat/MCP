from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogFilter


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        self.db.commit()

    def get_logs(self, filter: Optional[AuditLogFilter] = None, limit: int = 100) -> list[AuditLog]:
        """Get audit logs with optional filtering."""
        query = self.db.query(AuditLog)

        if filter:
            if filter.user_id is not None:
                query = query.filter(AuditLog.user_id == filter.user_id)
            if filter.action:
                query = query.filter(AuditLog.action == filter.action)
            if filter.resource_type:
                query = query.filter(AuditLog.resource_type == filter.resource_type)
            if filter.resource_id is not None:
                query = query.filter(AuditLog.resource_id == filter.resource_id)
            if filter.start_date:
                query = query.filter(AuditLog.created_at >= filter.start_date)
            if filter.end_date:
                query = query.filter(AuditLog.created_at <= filter.end_date)
            if filter.ip_address:
                query = query.filter(AuditLog.ip_address == filter.ip_address)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    def cleanup_old_logs(self, days: int = 90) -> None:
        """Clean up audit logs older than the specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        self.db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
        self.db.commit() 