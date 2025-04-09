from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKey,
    APIKeyList
)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

@router.post("", response_model=APIKey)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    db_api_key = APIKey(
        user_id=current_user.id,
        name=api_key.name,
        description=api_key.description
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

@router.get("", response_model=APIKeyList)
async def list_api_keys(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List API keys with pagination"""
    query = db.query(APIKey).filter(APIKey.user_id == current_user.id)
    
    total = query.count()
    api_keys = query.order_by(APIKey.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return APIKeyList(
        api_keys=api_keys,
        total=total,
        page=page,
        size=size
    )

@router.get("/{api_key_id}", response_model=APIKey)
async def get_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return api_key

@router.put("/{api_key_id}", response_model=APIKey)
async def update_api_key(
    api_key_id: int,
    api_key_update: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API key"""
    db_api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    for field, value in api_key_update.model_dump(exclude_unset=True).items():
        setattr(db_api_key, field, value)
    
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit() 