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
def test_alert(db: Session, test_user: User, test_api_key: APIKey):
    alert = Alert(
        type="response_time",
        level="warning",
        message="High response time detected",
        value=1.5,
        threshold=1.0,
        api_key_id=test_api_key.id,
        user_id=test_user.id,
        status="active"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@pytest.fixture
def auth_headers(test_user: User):
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

def test_get_alerts(db: Session, test_alert: Alert, auth_headers: dict):
    response = client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_alert.id
    assert data[0]["type"] == "response_time"
    assert data[0]["level"] == "warning"

def test_get_alerts_with_filters(db: Session, test_alert: Alert, auth_headers: dict):
    # Test type filter
    response = client.get("/api/v1/alerts?type=response_time", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    # Test level filter
    response = client.get("/api/v1/alerts?level=warning", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    # Test status filter
    response = client.get("/api/v1/alerts?status=active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

def test_get_alert_history(db: Session, test_alert: Alert, auth_headers: dict):
    response = client.get("/api/v1/alerts/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_alert.id

def test_get_alert_details(db: Session, test_alert: Alert, auth_headers: dict):
    response = client.get(f"/api/v1/alerts/{test_alert.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_alert.id
    assert data["type"] == "response_time"
    assert data["message"] == "High response time detected"

def test_acknowledge_alert(db: Session, test_alert: Alert, auth_headers: dict):
    response = client.post(
        f"/api/v1/alerts/{test_alert.id}/acknowledge",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None

def test_update_alert(db: Session, test_alert: Alert, auth_headers: dict):
    update_data = {
        "status": "resolved",
        "resolved_at": datetime.utcnow().isoformat()
    }
    response = client.put(
        f"/api/v1/alerts/{test_alert.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None

def test_get_alert_settings(auth_headers: dict):
    response = client.get("/api/v1/alerts/settings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "response_time" in data
    assert "error_rate" in data
    assert "usage_spike" in data

def test_update_alert_settings(auth_headers: dict):
    new_settings = {
        "response_time": {
            "warning": 1.5,
            "critical": 2.5
        }
    }
    response = client.put(
        "/api/v1/alerts/settings",
        json=new_settings,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response_time"]["warning"] == 1.5
    assert data["response_time"]["critical"] == 2.5

def test_unauthorized_access():
    response = client.get("/api/v1/alerts")
    assert response.status_code == 401

def test_invalid_alert_id(auth_headers: dict):
    response = client.get("/api/v1/alerts/999", headers=auth_headers)
    assert response.status_code == 404 