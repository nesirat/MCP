from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyInDB,
    APIKeyUsageStats
)
from app.services.api_key import APIKeyService
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=APIKeyInDB)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Create a new API key"""
    api_key_service = APIKeyService(db)
    return api_key_service.create_api_key(current_user.id, api_key_data)

@router.get("/", response_model=List[APIKeyInDB])
async def list_api_keys(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """List all API keys for the current user"""
    api_key_service = APIKeyService(db)
    return api_key_service.get_user_api_keys(current_user.id)

@router.get("/{key_id}", response_model=APIKeyInDB)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get a specific API key"""
    api_key_service = APIKeyService(db)
    api_key = api_key_service.get_api_key(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return api_key

@router.put("/{key_id}", response_model=APIKeyInDB)
async def update_api_key(
    key_id: int,
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Update an API key"""
    api_key_service = APIKeyService(db)
    api_key = api_key_service.get_api_key(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return api_key_service.update_api_key(key_id, api_key_data)

@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Delete an API key"""
    api_key_service = APIKeyService(db)
    api_key = api_key_service.get_api_key(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    if api_key_service.delete_api_key(key_id):
        return {"message": "API key deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to delete API key"
    )

@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get usage statistics for an API key"""
    api_key_service = APIKeyService(db)
    api_key = api_key_service.get_api_key(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return api_key_service.get_usage_stats(key_id) 