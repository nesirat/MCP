import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time

from app.main import app
from app.core.database import Base, engine
from app.models.user import User
from app.models.api_key import APIKey
from app.models.api_usage import APIUsage
from app.core.auth import create_access_token

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.rollback()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_api_key(db_session, test_user):
    api_key = APIKey(
        user_id=test_user.id,
        name="Test API Key",
        description="Test Description",
        key="test_api_key",
        is_active=True
    )
    db_session.add(api_key)
    db_session.commit()
    return api_key

def test_missing_api_key():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"

def test_invalid_api_key():
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

def test_inactive_api_key(db_session, test_user):
    # Create inactive API key
    api_key = APIKey(
        user_id=test_user.id,
        name="Inactive API Key",
        description="Test Description",
        key="inactive_key",
        is_active=False
    )
    db_session.add(api_key)
    db_session.commit()

    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": "inactive_key"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "API key is inactive"

def test_rate_limiting(db_session, test_api_key):
    # Make requests up to the rate limit
    for _ in range(100):  # Minute limit
        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"X-API-Key": test_api_key.key}
        )
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 429
    assert "Rate limit exceeded for minute" in response.json()["detail"]

def test_api_usage_logging(db_session, test_api_key):
    # Make an API request
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 200

    # Check if usage was logged
    usage = db_session.query(APIUsage).filter(
        APIUsage.api_key_id == test_api_key.id
    ).first()
    assert usage is not None
    assert usage.endpoint == "/api/v1/dashboard/stats"
    assert usage.method == "GET"
    assert usage.status_code == 200
    assert usage.response_time >= 0

def test_api_key_usage_update(db_session, test_api_key):
    # Make an API request
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 200

    # Check if API key usage was updated
    db_session.refresh(test_api_key)
    assert test_api_key.usage_count == 1
    assert test_api_key.last_used is not None

def test_rate_limit_headers(db_session, test_api_key):
    # Make an API request
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 200

    # Check rate limit headers
    assert "X-RateLimit-Minute-Limit" in response.headers
    assert "X-RateLimit-Minute-Remaining" in response.headers
    assert "X-RateLimit-Minute-Reset" in response.headers
    assert "X-RateLimit-Hour-Limit" in response.headers
    assert "X-RateLimit-Hour-Remaining" in response.headers
    assert "X-RateLimit-Hour-Reset" in response.headers
    assert "X-RateLimit-Day-Limit" in response.headers
    assert "X-RateLimit-Day-Remaining" in response.headers
    assert "X-RateLimit-Day-Reset" in response.headers

def test_rate_limit_reset(db_session, test_api_key):
    # Make requests up to the rate limit
    for _ in range(100):  # Minute limit
        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"X-API-Key": test_api_key.key}
        )
        assert response.status_code == 200

    # Wait for rate limit to reset
    time.sleep(61)

    # Next request should succeed
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 200

def test_error_handling(db_session, test_api_key):
    # Create a test endpoint that raises an exception
    @app.get("/test-error")
    async def test_error():
        raise Exception("Test error")

    # Make request to error endpoint
    response = client.get(
        "/test-error",
        headers={"X-API-Key": test_api_key.key}
    )
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]

def test_non_api_routes(db_session, test_api_key):
    # Test that non-API routes are not affected by the middleware
    response = client.get("/")
    assert response.status_code == 200

    response = client.get("/login")
    assert response.status_code == 200

    response = client.get("/dashboard")
    assert response.status_code == 200 