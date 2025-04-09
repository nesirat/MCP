from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
    NotificationLogResponse
)
from app.core.auth import get_current_user
from app.models.notification import NotificationConfig, NotificationLog
from app.services.notification import NotificationService

router = APIRouter()

@router.post("/", response_model=NotificationConfigResponse)
async def create_notification_config(
    config: NotificationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = NotificationConfig(
        user_id=current_user.id,
        **config.dict()
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/", response_model=List[NotificationConfigResponse])
async def list_notification_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(NotificationConfig).filter(
        NotificationConfig.user_id == current_user.id
    ).all()

@router.get("/{config_id}", response_model=NotificationConfigResponse)
async def get_notification_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(NotificationConfig).filter(
        NotificationConfig.id == config_id,
        NotificationConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification config not found"
        )
    return config

@router.put("/{config_id}", response_model=NotificationConfigResponse)
async def update_notification_config(
    config_id: int,
    config_update: NotificationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = db.query(NotificationConfig).filter(
        NotificationConfig.id == config_id,
        NotificationConfig.user_id == current_user.id
    ).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification config not found"
        )

    for field, value in config_update.dict(exclude_unset=True).items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)
    return db_config

@router.delete("/{config_id}")
async def delete_notification_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = db.query(NotificationConfig).filter(
        NotificationConfig.id == config_id,
        NotificationConfig.user_id == current_user.id
    ).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification config not found"
        )

    db.delete(db_config)
    db.commit()
    return {"message": "Notification config deleted"}

@router.get("/{config_id}/logs", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(NotificationConfig).filter(
        NotificationConfig.id == config_id,
        NotificationConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification config not found"
        )

    return db.query(NotificationLog).filter(
        NotificationLog.notification_config_id == config_id
    ).order_by(NotificationLog.created_at.desc()).all()

@router.post("/{config_id}/test")
async def test_notification_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(NotificationConfig).filter(
        NotificationConfig.id == config_id,
        NotificationConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification config not found"
        )

    # Create a test alert
    test_alert = {
        "type": "test",
        "level": "info",
        "message": "This is a test notification",
        "value": 0,
        "threshold": 0
    }

    notification_service = NotificationService(db)
    success = await notification_service.send_notification(test_alert, config)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )

    return {"message": "Test notification sent successfully"} 