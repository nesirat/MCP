import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.core.database import Base, engine
from app.models.user import User
from app.models.ticket import Ticket
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
def test_token(test_user):
    return create_access_token({"sub": test_user.email})

@pytest.fixture
def test_tickets(db_session, test_user):
    tickets = [
        Ticket(
            user_id=test_user.id,
            subject="Test Ticket 1",
            description="Description 1",
            status="open"
        ),
        Ticket(
            user_id=test_user.id,
            subject="Test Ticket 2",
            description="Description 2",
            status="resolved"
        ),
        Ticket(
            user_id=test_user.id,
            subject="Test Ticket 3",
            description="Description 3",
            status="open"
        )
    ]
    for ticket in tickets:
        db_session.add(ticket)
    db_session.commit()
    return tickets

@pytest.fixture
def test_api_keys(db_session, test_user):
    api_keys = [
        APIKey(
            user_id=test_user.id,
            name="Test Key 1",
            description="Description 1",
            key="key1",
            is_active=True
        ),
        APIKey(
            user_id=test_user.id,
            name="Test Key 2",
            description="Description 2",
            key="key2",
            is_active=False
        )
    ]
    for api_key in api_keys:
        db_session.add(api_key)
    db_session.commit()
    return api_keys

@pytest.fixture
def test_api_usage(db_session, test_user, test_api_keys):
    usage_records = [
        APIUsage(
            user_id=test_user.id,
            api_key_id=test_api_keys[0].id,
            endpoint="/test/endpoint1",
            method="GET",
            status_code=200,
            response_time=0.1
        ),
        APIUsage(
            user_id=test_user.id,
            api_key_id=test_api_keys[0].id,
            endpoint="/test/endpoint2",
            method="POST",
            status_code=400,
            response_time=0.2
        ),
        APIUsage(
            user_id=test_user.id,
            api_key_id=test_api_keys[1].id,
            endpoint="/test/endpoint3",
            method="GET",
            status_code=200,
            response_time=0.15
        )
    ]
    for usage in usage_records:
        db_session.add(usage)
    db_session.commit()
    return usage_records

def test_get_dashboard_stats_unauthorized():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401

def test_get_dashboard_stats_success(test_token, test_tickets, test_api_keys, test_api_usage):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/dashboard/stats", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check ticket counts
    assert data["open_tickets"] == 2
    assert data["resolved_tickets"] == 1
    
    # Check API key counts
    assert data["active_api_keys"] == 1
    assert data["total_api_calls"] == 3
    
    # Check API usage statistics
    assert data["api_usage"]["success_rate"] == pytest.approx(66.67, rel=1e-2)
    assert data["api_usage"]["avg_response_time"] == pytest.approx(0.15, rel=1e-2)
    
    # Check recent tickets
    assert len(data["recent_tickets"]) == 3
    assert all(ticket["status"] in ["open", "resolved"] for ticket in data["recent_tickets"])
    
    # Check API keys
    assert len(data["api_keys"]) == 2
    assert data["api_keys"][0]["usage_count"] == 2
    assert data["api_keys"][1]["usage_count"] == 1

def test_get_dashboard_stats_no_data(test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/dashboard/stats", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all counts are zero
    assert data["open_tickets"] == 0
    assert data["resolved_tickets"] == 0
    assert data["active_api_keys"] == 0
    assert data["total_api_calls"] == 0
    
    # Check API usage statistics
    assert data["api_usage"]["success_rate"] == 0
    assert data["api_usage"]["avg_response_time"] == 0
    
    # Check empty lists
    assert len(data["recent_tickets"]) == 0
    assert len(data["api_keys"]) == 0

def test_get_dashboard_stats_with_pagination(test_token, test_tickets, test_api_keys, test_api_usage):
    # Create more tickets to test pagination
    for i in range(4, 8):
        ticket = Ticket(
            user_id=test_tickets[0].user_id,
            subject=f"Test Ticket {i}",
            description=f"Description {i}",
            status="open"
        )
        test_tickets.append(ticket)
    
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/dashboard/stats", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that only the 5 most recent tickets are returned
    assert len(data["recent_tickets"]) == 5
    assert all(ticket["status"] == "open" for ticket in data["recent_tickets"][:4])
    assert data["recent_tickets"][4]["status"] == "resolved" 