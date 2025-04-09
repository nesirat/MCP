from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    AnalyticsFilter,
    AnalyticsSummary,
    APITrendResponse,
)
from app.core.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    filter: Optional[AnalyticsFilter] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get analytics summary with optional filtering."""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_analytics_summary(filter)


@router.get("/trends/{api_id}", response_model=list[APITrendResponse])
async def get_api_trends(
    api_id: int,
    period: int = 60,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get trend data for a specific API."""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_trend_data(api_id, period, limit)


@router.post("/cleanup")
async def cleanup_analytics_data(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clean up old analytics data."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can perform cleanup operations",
        )
    
    analytics_service = AnalyticsService(db)
    analytics_service.cleanup_old_data(days)
    return {"message": f"Cleaned up analytics data older than {days} days"} 