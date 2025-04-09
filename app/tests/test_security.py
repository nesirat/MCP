from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.rate_limit import RateLimit
from app.services.rate_limit import RateLimitService
from app.services.audit import AuditService
from app.schemas.rate_limit import RateLimitConfig


def test_rate_limiting(client: TestClient, auth_headers: dict, test_user):
    """Test rate limiting functionality."""
    # Configure rate limit for testing
    config = RateLimitConfig(limit=2, window=60)
    
    # Make requests within limit
    for _ in range(2):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
    
    # Make request exceeding limit
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_audit_logging(client: TestClient, auth_headers: dict, test_user, db: Session):
    """Test audit logging functionality."""
    # Make a request
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    # Check audit log
    audit_log = db.query(AuditLog).first()
    assert audit_log is not None
    assert audit_log.user_id == test_user.id
    assert audit_log.action == "GET"
    assert audit_log.resource_type == "endpoint"
    assert "/api/auth/me" in audit_log.details
    assert audit_log.ip_address is not None
    assert audit_log.user_agent is not None


def test_rate_limit_service(db: Session, test_user):
    """Test rate limit service directly."""
    service = RateLimitService(db)
    config = RateLimitConfig(limit=2, window=60)
    
    # Test within limit
    for _ in range(2):
        service.check_rate_limit(test_user.id, "/test", config)
    
    # Test exceeding limit
    try:
        service.check_rate_limit(test_user.id, "/test", config)
        assert False, "Should have raised rate limit exception"
    except Exception as e:
        assert "Rate limit exceeded" in str(e)
    
    # Test cleanup
    service.cleanup_expired_limits()
    limits = db.query(RateLimit).all()
    assert len(limits) == 1  # Only the current window should remain


def test_audit_service(db: Session, test_user):
    """Test audit service directly."""
    service = AuditService(db)
    
    # Log an event
    service.log(
        action="TEST",
        resource_type="test",
        user_id=test_user.id,
        details="Test audit log",
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    
    # Check log was created
    log = db.query(AuditLog).first()
    assert log is not None
    assert log.action == "TEST"
    assert log.user_id == test_user.id
    assert log.details == "Test audit log"
    
    # Test filtering
    logs = service.get_logs(limit=10)
    assert len(logs) == 1
    
    # Test cleanup
    service.cleanup_old_logs(days=0)  # Clean up all logs
    logs = service.get_logs(limit=10)
    assert len(logs) == 0


def test_security_middleware(client: TestClient, auth_headers: dict, test_user, db: Session):
    """Test security middleware integration."""
    # Make a request
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    # Check both rate limit and audit log were created
    rate_limit = db.query(RateLimit).first()
    assert rate_limit is not None
    assert rate_limit.user_id == test_user.id
    
    audit_log = db.query(AuditLog).first()
    assert audit_log is not None
    assert audit_log.user_id == test_user.id 