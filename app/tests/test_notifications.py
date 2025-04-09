import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.notification import NotificationConfig, NotificationLog
from app.schemas.notification import NotificationType

def test_create_notification(client: TestClient, db: Session, test_user, auth_headers):
    # Test email notification
    email_data = {
        "name": "Email Alert",
        "type": "email",
        "enabled": True,
        "config": {
            "recipients": ["test@example.com"],
            "subject_template": "Alert: {{alert.type}}"
        }
    }
    response = client.post("/api/notifications", json=email_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == email_data["name"]
    assert data["type"] == email_data["type"]
    assert data["enabled"] == email_data["enabled"]

    # Test webhook notification
    webhook_data = {
        "name": "Webhook Alert",
        "type": "webhook",
        "enabled": True,
        "config": {
            "url": "https://example.com/webhook",
            "method": "POST"
        }
    }
    response = client.post("/api/notifications", json=webhook_data, headers=auth_headers)
    assert response.status_code == 200

    # Test invalid notification type
    invalid_data = {
        "name": "Invalid Alert",
        "type": "invalid",
        "enabled": True,
        "config": {}
    }
    response = client.post("/api/notifications", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422

def test_list_notifications(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notifications
    notification1 = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification 1",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    notification2 = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification 2",
        type=NotificationType.WEBHOOK,
        enabled=False,
        config={"url": "https://example.com/webhook"}
    )
    db.add_all([notification1, notification2])
    db.commit()

    response = client.get("/api/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(n["name"] == "Test Notification 1" for n in data)
    assert any(n["name"] == "Test Notification 2" for n in data)

def test_get_notification(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notification
    notification = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    db.add(notification)
    db.commit()

    response = client.get(f"/api/notifications/{notification.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == notification.name
    assert data["type"] == notification.type

    # Test non-existent notification
    response = client.get("/api/notifications/999", headers=auth_headers)
    assert response.status_code == 404

def test_update_notification(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notification
    notification = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    db.add(notification)
    db.commit()

    update_data = {
        "name": "Updated Notification",
        "enabled": False
    }
    response = client.put(f"/api/notifications/{notification.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["enabled"] == update_data["enabled"]

    # Test update with invalid data
    invalid_data = {
        "type": "invalid"
    }
    response = client.put(f"/api/notifications/{notification.id}", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422

def test_delete_notification(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notification
    notification = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    db.add(notification)
    db.commit()

    response = client.delete(f"/api/notifications/{notification.id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/api/notifications/{notification.id}", headers=auth_headers)
    assert response.status_code == 404

def test_get_notification_logs(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notification and logs
    notification = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    db.add(notification)
    db.commit()

    log1 = NotificationLog(
        notification_config_id=notification.id,
        alert_id=1,
        status="success",
        created_at=datetime.utcnow()
    )
    log2 = NotificationLog(
        notification_config_id=notification.id,
        alert_id=2,
        status="error",
        error_message="Failed to send",
        created_at=datetime.utcnow()
    )
    db.add_all([log1, log2])
    db.commit()

    response = client.get(f"/api/notifications/{notification.id}/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(log["status"] == "success" for log in data)
    assert any(log["status"] == "error" for log in data)

def test_test_notification(client: TestClient, db: Session, test_user, auth_headers):
    # Create test notification
    notification = NotificationConfig(
        user_id=test_user.id,
        name="Test Notification",
        type=NotificationType.EMAIL,
        enabled=True,
        config={"recipients": ["test@example.com"]}
    )
    db.add(notification)
    db.commit()

    response = client.post(f"/api/notifications/{notification.id}/test", headers=auth_headers)
    assert response.status_code == 200

    # Verify test log was created
    logs = db.query(NotificationLog).filter(
        NotificationLog.notification_config_id == notification.id
    ).all()
    assert len(logs) == 1
    assert logs[0].status in ["success", "error"]

def test_unauthorized_access(client: TestClient):
    # Test all endpoints without authentication
    response = client.get("/api/notifications")
    assert response.status_code == 401

    response = client.post("/api/notifications", json={})
    assert response.status_code == 401

    response = client.get("/api/notifications/1")
    assert response.status_code == 401

    response = client.put("/api/notifications/1", json={})
    assert response.status_code == 401

    response = client.delete("/api/notifications/1")
    assert response.status_code == 401

    response = client.get("/api/notifications/1/logs")
    assert response.status_code == 401

    response = client.post("/api/notifications/1/test")
    assert response.status_code == 401 