from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.analytics import APIAnalytics, APITrend
from app.schemas.analytics import AnalyticsFilter, TimeRange


def test_record_api_call(analytics_service, test_api):
    """Test recording an API call."""
    analytics_service.record_api_call(
        api_id=test_api.id,
        response_time=0.5,
        status_code=200,
        success=True,
    )
    
    analytics = analytics_service.db.query(APIAnalytics).first()
    assert analytics is not None
    assert analytics.api_id == test_api.id
    assert analytics.response_time == 0.5
    assert analytics.status_code == 200
    assert analytics.success == 1
    assert analytics.error_count == 0
    assert analytics.request_count == 1


def test_calculate_trends(analytics_service, test_api):
    """Test calculating trends for an API."""
    # Record some API calls
    for i in range(5):
        analytics_service.record_api_call(
            api_id=test_api.id,
            response_time=0.5 + i * 0.1,
            status_code=200,
            success=True,
        )
    
    analytics_service.calculate_trends(test_api.id)
    
    trend = analytics_service.db.query(APITrend).first()
    assert trend is not None
    assert trend.api_id == test_api.id
    assert trend.period == 60
    assert trend.success_rate == 1.0
    assert trend.error_rate == 0.0
    assert trend.request_count == 5


def test_get_analytics_summary(analytics_service, test_api):
    """Test getting analytics summary."""
    # Record some API calls
    for i in range(5):
        analytics_service.record_api_call(
            api_id=test_api.id,
            response_time=0.5 + i * 0.1,
            status_code=200,
            success=True,
        )
    
    summary = analytics_service.get_analytics_summary()
    assert summary.total_requests == 5
    assert summary.total_errors == 0
    assert summary.success_rate == 1.0
    assert summary.error_rate == 0.0


def test_get_analytics_summary_with_filter(analytics_service, test_api):
    """Test getting analytics summary with time filter."""
    # Record some API calls
    for i in range(5):
        analytics_service.record_api_call(
            api_id=test_api.id,
            response_time=0.5 + i * 0.1,
            status_code=200,
            success=True,
        )
    
    # Create a time filter for the last hour
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    time_filter = AnalyticsFilter(
        time_range=TimeRange(start_time=start_time, end_time=end_time)
    )
    
    summary = analytics_service.get_analytics_summary(time_filter)
    assert summary.total_requests == 5


def test_get_trend_data(analytics_service, test_api):
    """Test getting trend data for an API."""
    # Record some API calls and calculate trends
    for i in range(5):
        analytics_service.record_api_call(
            api_id=test_api.id,
            response_time=0.5 + i * 0.1,
            status_code=200,
            success=True,
        )
        analytics_service.calculate_trends(test_api.id)
    
    trends = analytics_service.get_trend_data(test_api.id)
    assert len(trends) == 5
    assert all(trend.api_id == test_api.id for trend in trends)
    assert all(trend.period == 60 for trend in trends)


def test_cleanup_old_data(analytics_service, test_api):
    """Test cleaning up old analytics data."""
    # Record some old API calls
    old_time = datetime.utcnow() - timedelta(days=31)
    analytics = APIAnalytics(
        api_id=test_api.id,
        timestamp=old_time,
        response_time=0.5,
        status_code=200,
        success=1,
        error_count=0,
        request_count=1,
    )
    analytics_service.db.add(analytics)
    analytics_service.db.commit()
    
    # Record some recent API calls
    analytics_service.record_api_call(
        api_id=test_api.id,
        response_time=0.5,
        status_code=200,
        success=True,
    )
    
    # Clean up data older than 30 days
    analytics_service.cleanup_old_data()
    
    # Check that only recent data remains
    remaining_analytics = analytics_service.db.query(APIAnalytics).all()
    assert len(remaining_analytics) == 1
    assert remaining_analytics[0].timestamp > datetime.utcnow() - timedelta(days=30)


def test_analytics_endpoints(client, auth_headers, test_api):
    """Test analytics API endpoints."""
    # Test getting analytics summary
    response = client.get("/api/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_errors" in data
    assert "avg_response_time" in data
    assert "success_rate" in data
    assert "error_rate" in data
    assert "recent_trends" in data
    
    # Test getting trend data
    response = client.get(
        f"/api/analytics/trends/{test_api.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Test cleanup endpoint (should fail for non-superuser)
    response = client.post(
        "/api/analytics/cleanup",
        headers=auth_headers
    )
    assert response.status_code == 403 