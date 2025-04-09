import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.models.api import API
from app.core.auth import get_password_hash
from app.services.analytics import AnalyticsService


@pytest.fixture(scope="session")
def test_db():
    # Create test database
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(test_db):
    return TestClient(app)


@pytest.fixture(scope="session")
def test_user(test_db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="session")
def test_api(test_db, test_user):
    api = API(
        name="Test API",
        url="https://api.example.com",
        method="GET",
        user_id=test_user.id,
    )
    test_db.add(api)
    test_db.commit()
    test_db.refresh(api)
    return api


@pytest.fixture(scope="session")
def analytics_service(test_db):
    return AnalyticsService(test_db)


@pytest.fixture(scope="session")
def auth_headers(client, test_user):
    # Login to get token
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "testpassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"} 