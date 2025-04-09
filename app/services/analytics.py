from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.analytics import APIAnalytics, APITrend
from app.schemas.analytics import (
    APIAnalyticsCreate,
    APITrendCreate,
    AnalyticsFilter,
    AnalyticsSummary,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def record_api_call(
        self,
        api_id: int,
        response_time: float,
        status_code: int,
        success: bool,
        error_count: int = 0,
    ) -> None:
        """Record an API call in the analytics database."""
        analytics = APIAnalytics(
            api_id=api_id,
            response_time=response_time,
            status_code=status_code,
            success=1 if success else 0,
            error_count=error_count,
        )
        self.db.add(analytics)
        self.db.commit()

    def calculate_trends(
        self, api_id: int, period: int = 60
    ) -> None:
        """Calculate trends for a specific API over a given period."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=period)

        # Get analytics data for the period
        analytics = (
            self.db.query(APIAnalytics)
            .filter(
                and_(
                    APIAnalytics.api_id == api_id,
                    APIAnalytics.timestamp >= start_time,
                    APIAnalytics.timestamp <= end_time,
                )
            )
            .all()
        )

        if not analytics:
            return

        # Calculate metrics
        total_requests = len(analytics)
        total_errors = sum(a.error_count for a in analytics)
        avg_response_time = sum(a.response_time for a in analytics) / total_requests
        success_rate = sum(a.success for a in analytics) / total_requests
        error_rate = total_errors / total_requests

        # Create trend record
        trend = APITrend(
            api_id=api_id,
            period=period,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            request_count=total_requests,
            error_count=total_errors,
        )
        self.db.add(trend)
        self.db.commit()

    def get_analytics_summary(
        self, filter: Optional[AnalyticsFilter] = None
    ) -> AnalyticsSummary:
        """Get a summary of analytics data with optional filtering."""
        query = self.db.query(APIAnalytics)

        if filter and filter.time_range:
            query = query.filter(
                and_(
                    APIAnalytics.timestamp >= filter.time_range.start_time,
                    APIAnalytics.timestamp <= filter.time_range.end_time,
                )
            )

        if filter and filter.api_id:
            query = query.filter(APIAnalytics.api_id == filter.api_id)

        analytics = query.all()

        if not analytics:
            return AnalyticsSummary(
                total_requests=0,
                total_errors=0,
                avg_response_time=0,
                success_rate=0,
                error_rate=0,
                recent_trends=[],
            )

        total_requests = len(analytics)
        total_errors = sum(a.error_count for a in analytics)
        avg_response_time = sum(a.response_time for a in analytics) / total_requests
        success_rate = sum(a.success for a in analytics) / total_requests
        error_rate = total_errors / total_requests

        # Get recent trends
        period = filter.period if filter and filter.api_id else 60
        recent_trends = (
            self.db.query(APITrend)
            .filter(APITrend.api_id == filter.api_id if filter and filter.api_id else True)
            .order_by(APITrend.timestamp.desc())
            .limit(10)
            .all()
        )

        return AnalyticsSummary(
            total_requests=total_requests,
            total_errors=total_errors,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            recent_trends=recent_trends,
        )

    def get_trend_data(
        self, api_id: int, period: int = 60, limit: int = 100
    ) -> List[APITrend]:
        """Get trend data for a specific API."""
        return (
            self.db.query(APITrend)
            .filter(APITrend.api_id == api_id, APITrend.period == period)
            .order_by(APITrend.timestamp.desc())
            .limit(limit)
            .all()
        )

    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up analytics data older than the specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old analytics data
        self.db.query(APIAnalytics).filter(
            APIAnalytics.timestamp < cutoff_date
        ).delete()
        
        # Delete old trend data
        self.db.query(APITrend).filter(
            APITrend.timestamp < cutoff_date
        ).delete()
        
        self.db.commit() 