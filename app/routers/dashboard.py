from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.api_key import APIKey
from app.models.api_usage import APIUsage
from app.schemas.dashboard import DashboardStats, RecentTicket, APIUsageData

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the current user."""
    try:
        # Get ticket counts
        open_tickets = db.query(Ticket).filter(
            Ticket.user_id == current_user.id,
            Ticket.status == "open"
        ).count()
        
        resolved_tickets = db.query(Ticket).filter(
            Ticket.user_id == current_user.id,
            Ticket.status == "resolved"
        ).count()

        # Get API key statistics
        active_api_keys = db.query(APIKey).filter(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).count()

        # Get API usage statistics
        total_api_calls = db.query(APIUsage).filter(
            APIUsage.user_id == current_user.id
        ).count()

        # Calculate success rate and average response time
        success_count = db.query(APIUsage).filter(
            APIUsage.user_id == current_user.id,
            APIUsage.status_code >= 200,
            APIUsage.status_code < 300
        ).count()

        avg_response_time = db.query(func.avg(APIUsage.response_time)).filter(
            APIUsage.user_id == current_user.id
        ).scalar() or 0

        success_rate = (success_count / total_api_calls * 100) if total_api_calls > 0 else 0

        # Get recent tickets
        recent_tickets = db.query(Ticket).filter(
            Ticket.user_id == current_user.id
        ).order_by(Ticket.created_at.desc()).limit(5).all()

        # Get API keys with usage
        api_keys = db.query(APIKey).filter(
            APIKey.user_id == current_user.id
        ).all()

        # Format recent tickets
        formatted_tickets = [
            RecentTicket(
                id=ticket.id,
                subject=ticket.subject,
                status=ticket.status,
                created_at=ticket.created_at
            )
            for ticket in recent_tickets
        ]

        # Format API keys
        formatted_api_keys = []
        for api_key in api_keys:
            usage_count = db.query(APIUsage).filter(
                APIUsage.api_key_id == api_key.id
            ).count()

            last_used = db.query(APIUsage).filter(
                APIUsage.api_key_id == api_key.id
            ).order_by(APIUsage.created_at.desc()).first()

            formatted_api_keys.append({
                "id": api_key.id,
                "name": api_key.name,
                "is_active": api_key.is_active,
                "usage_count": usage_count,
                "last_used": last_used.created_at if last_used else None
            })

        # Create API usage data
        api_usage = APIUsageData(
            success_rate=success_rate,
            avg_response_time=float(avg_response_time)
        )

        return DashboardStats(
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            active_api_keys=active_api_keys,
            total_api_calls=total_api_calls,
            api_usage=api_usage,
            recent_tickets=formatted_tickets,
            api_keys=formatted_api_keys
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard statistics: {str(e)}"
        ) 