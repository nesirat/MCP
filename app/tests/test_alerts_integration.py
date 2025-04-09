import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.alert import Alert
from app.models.user import User
from app.models.api_key import APIKey
from app.core.auth import create_access_token

client = TestClient(app)

@pytest.fixture
def test_user(db: Session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_api_key(db: Session, test_user: User):
    api_key = APIKey(
        user_id=test_user.id,
        name="Test API Key",
        description="Test Description",
        key="test_api_key",
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

@pytest.fixture
def auth_headers(test_user: User):
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

def test_alert_creation_scenarios(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Test response time alert
    response = client.post(
        "/api/v1/alerts",
        json={
            "type": "response_time",
            "level": "warning",
            "message": "High response time detected",
            "value": 1.5,
            "threshold": 1.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "response_time"
    assert data["level"] == "warning"
    assert data["status"] == "active"

    # Test error rate alert
    response = client.post(
        "/api/v1/alerts",
        json={
            "type": "error_rate",
            "level": "critical",
            "message": "High error rate detected",
            "value": 15.0,
            "threshold": 10.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "error_rate"
    assert data["level"] == "critical"

def test_alert_filtering_scenarios(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Create multiple alerts with different types and levels
    alerts = [
        {
            "type": "response_time",
            "level": "warning",
            "message": "High response time",
            "value": 1.5,
            "threshold": 1.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        {
            "type": "error_rate",
            "level": "critical",
            "message": "High error rate",
            "value": 15.0,
            "threshold": 10.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        }
    ]

    for alert_data in alerts:
        client.post("/api/v1/alerts", json=alert_data, headers=auth_headers)

    # Test filtering by type
    response = client.get("/api/v1/alerts?type=response_time", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(alert["type"] == "response_time" for alert in data)

    # Test filtering by level
    response = client.get("/api/v1/alerts?level=critical", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(alert["level"] == "critical" for alert in data)

    # Test filtering by time range
    response = client.get("/api/v1/alerts?timeRange=24h", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_alert_acknowledgment_flow(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Create an alert
    response = client.post(
        "/api/v1/alerts",
        json={
            "type": "response_time",
            "level": "warning",
            "message": "High response time",
            "value": 1.5,
            "threshold": 1.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        headers=auth_headers
    )
    alert_id = response.json()["id"]

    # Acknowledge the alert
    response = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None

    # Try to acknowledge again (should fail)
    response = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers=auth_headers
    )
    assert response.status_code == 400

def test_alert_resolution_flow(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Create an alert
    response = client.post(
        "/api/v1/alerts",
        json={
            "type": "response_time",
            "level": "warning",
            "message": "High response time",
            "value": 1.5,
            "threshold": 1.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        headers=auth_headers
    )
    alert_id = response.json()["id"]

    # Resolve the alert
    response = client.put(
        f"/api/v1/alerts/{alert_id}",
        json={
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None

    # Try to resolve again (should fail)
    response = client.put(
        f"/api/v1/alerts/{alert_id}",
        json={
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat()
        },
        headers=auth_headers
    )
    assert response.status_code == 400

def test_alert_settings_validation(db: Session, auth_headers: dict):
    # Test valid settings
    valid_settings = {
        "response_time": {
            "warning": 1.0,
            "critical": 2.0
        },
        "error_rate": {
            "warning": 5.0,
            "critical": 10.0
        },
        "usage_spike": {
            "warning": 50.0,
            "critical": 100.0
        }
    }

    response = client.put(
        "/api/v1/alerts/settings",
        json=valid_settings,
        headers=auth_headers
    )
    assert response.status_code == 200

    # Test invalid settings (negative values)
    invalid_settings = {
        "response_time": {
            "warning": -1.0,
            "critical": 2.0
        }
    }

    response = client.put(
        "/api/v1/alerts/settings",
        json=invalid_settings,
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test invalid settings (warning > critical)
    invalid_settings = {
        "response_time": {
            "warning": 3.0,
            "critical": 2.0
        }
    }

    response = client.put(
        "/api/v1/alerts/settings",
        json=invalid_settings,
        headers=auth_headers
    )
    assert response.status_code == 422

def test_alert_history_pagination(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Create multiple alerts
    for i in range(15):
        client.post(
            "/api/v1/alerts",
            json={
                "type": "response_time",
                "level": "warning",
                "message": f"Alert {i}",
                "value": 1.5,
                "threshold": 1.0,
                "api_key_id": test_api_key.id,
                "user_id": test_user.id
            },
            headers=auth_headers
        )

    # Test pagination
    response = client.get("/api/v1/alerts/history?page=1&per_page=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    response = client.get("/api/v1/alerts/history?page=2&per_page=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_alert_cleanup(db: Session, test_user: User, test_api_key: APIKey, auth_headers: dict):
    # Create old alerts
    old_date = datetime.utcnow() - timedelta(days=91)
    alert = Alert(
        type="response_time",
        level="warning",
        message="Old alert",
        value=1.5,
        threshold=1.0,
        api_key_id=test_api_key.id,
        user_id=test_user.id,
        created_at=old_date
    )
    db.add(alert)
    db.commit()

    # Create recent alert
    client.post(
        "/api/v1/alerts",
        json={
            "type": "response_time",
            "level": "warning",
            "message": "Recent alert",
            "value": 1.5,
            "threshold": 1.0,
            "api_key_id": test_api_key.id,
            "user_id": test_user.id
        },
        headers=auth_headers
    )

    # Get alerts (should only return recent ones)
    response = client.get("/api/v1/alerts/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message"] == "Recent alert" 