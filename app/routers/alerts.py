from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    level: Optional[str] = Query(None, description="Filter by alert level"),
    status: Optional[str] = Query(None, description="Filter by alert status"),
    date_range: Optional[str] = Query("24h", description="Time range for alerts")
):
    """Get active alerts with optional filtering."""
    query = db.query(Alert)

    # Apply filters
    if alert_type:
        query = query.filter(Alert.type == alert_type)
    if level:
        query = query.filter(Alert.level == level)
    if status:
        query = query.filter(Alert.status == status)

    # Apply date range
    now = datetime.utcnow()
    if date_range == "24h":
        query = query.filter(Alert.created_at >= now - timedelta(hours=24))
    elif date_range == "7d":
        query = query.filter(Alert.created_at >= now - timedelta(days=7))
    elif date_range == "30d":
        query = query.filter(Alert.created_at >= now - timedelta(days=30))

    return query.order_by(Alert.created_at.desc()).all()

@router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    level: Optional[str] = Query(None, description="Filter by alert level"),
    status: Optional[str] = Query(None, description="Filter by alert status"),
    date_range: Optional[str] = Query("7d", description="Time range for alerts")
):
    """Get alert history with optional filtering."""
    return await get_alerts(
        db=db,
        current_user=current_user,
        alert_type=alert_type,
        level=level,
        status=status,
        date_range=date_range
    )

@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get details of a specific alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    return alert

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    for field, value in alert_update.dict(exclude_unset=True).items():
        setattr(alert, field, value)
    
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/alerts/settings", response_model=dict)
async def get_alert_settings(
    current_user = Depends(get_current_user)
):
    """Get current alert settings."""
    from app.core.alerts import AlertService
    return AlertService.alert_thresholds

@router.put("/alerts/settings", response_model=dict)
async def update_alert_settings(
    settings: dict,
    current_user = Depends(get_current_user)
):
    """Update alert settings."""
    from app.core.alerts import AlertService
    AlertService.alert_thresholds.update(settings)
    return AlertService.alert_thresholds 