from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate


def test_register(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == data["email"]
    assert content["username"] == data["username"]
    assert "id" in content
    assert "hashed_password" not in content


def test_register_existing_email(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this email already exists in the system."


def test_register_existing_username(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    data["email"] = "test2@example.com"
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this username already exists in the system."


def test_login(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    login_data = {
        "username": data["username"],
        "password": data["password"],
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    content = response.json()
    assert "access_token" in content
    assert content["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    login_data = {
        "username": data["username"],
        "password": "wrongpassword",
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_inactive_user(client: TestClient, db: Session) -> None:
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "is_active": False,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    login_data = {
        "username": data["username"],
        "password": data["password"],
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


def test_read_users_me(client: TestClient, db: Session, test_user, auth_headers) -> None:
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == test_user.email
    assert content["username"] == test_user.username
    assert "id" in content
    assert "hashed_password" not in content


def test_update_user_me(client: TestClient, db: Session, test_user, auth_headers) -> None:
    data = {
        "username": "newusername",
        "email": "newemail@example.com",
        "password": "newpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.put("/api/auth/me", json=data, headers=auth_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == data["email"]
    assert content["username"] == data["username"]
    assert "id" in content
    assert "hashed_password" not in content


def test_update_user_me_existing_email(client: TestClient, db: Session, test_user, auth_headers) -> None:
    # Create another user
    data = {
        "username": "otheruser",
        "email": "other@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    # Try to update with existing email
    update_data = {
        "email": "other@example.com",
    }
    response = client.put("/api/auth/me", json=update_data, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this email already exists in the system."


def test_update_user_me_existing_username(client: TestClient, db: Session, test_user, auth_headers) -> None:
    # Create another user
    data = {
        "username": "otheruser",
        "email": "other@example.com",
        "password": "testpassword",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 200
    # Try to update with existing username
    update_data = {
        "username": "otheruser",
    }
    response = client.put("/api/auth/me", json=update_data, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this username already exists in the system." 