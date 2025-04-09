from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import List, Dict
from datetime import datetime

from app.core.config import settings
from app.core.auth import get_current_active_user
from app.schemas.user import User

router = APIRouter()


@router.get("/versions", response_model=List[Dict])
async def get_supported_versions(request: Request):
    """Get list of supported API versions with their status."""
    versioning_middleware = request.app.state.versioning_middleware
    versions = []
    
    for version, data in versioning_middleware.version_data.items():
        version_info = {
            "version": version,
            "status": "deprecated" if data.deprecated else "active",
            "deprecated": data.deprecated,
        }
        if data.sunset_date:
            version_info["sunset_date"] = data.sunset_date.isoformat()
        versions.append(version_info)
    
    return versions


@router.get("/current-version")
async def get_current_version():
    """Get current API version."""
    return {
        "version": settings.CURRENT_API_VERSION,
        "status": "active",
        "docs_url": settings.API_DOCS_URL,
        "openapi_url": settings.API_OPENAPI_URL,
        "latest_version": max(settings.SUPPORTED_API_VERSIONS)
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "api_version": settings.CURRENT_API_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/info")
async def api_info(current_user: User = Depends(get_current_active_user)):
    """Get detailed API information."""
    return {
        "title": settings.API_TITLE,
        "description": settings.API_DESCRIPTION,
        "version": settings.API_VERSION,
        "api_version": settings.CURRENT_API_VERSION,
        "contact": settings.API_CONTACT,
        "license": settings.API_LICENSE,
        "terms_of_service": settings.API_TERMS_OF_SERVICE,
        "docs_url": settings.API_DOCS_URL,
        "redoc_url": settings.API_REDOC_URL,
        "openapi_url": settings.API_OPENAPI_URL,
        "supported_versions": settings.SUPPORTED_API_VERSIONS,
        "latest_version": max(settings.SUPPORTED_API_VERSIONS),
        "environment": settings.ENVIRONMENT,
        "features": {
            "rate_limiting": True,
            "authentication": True,
            "documentation": True,
            "versioning": True,
            "monitoring": True
        }
    }


@router.get("/changelog")
async def get_changelog(current_user: User = Depends(get_current_active_user)):
    """Get API changelog."""
    return {
        "versions": [
            {
                "version": "v2",
                "release_date": "2024-01-01",
                "changes": [
                    "Added new endpoints for advanced analytics",
                    "Improved rate limiting with more granular controls",
                    "Enhanced security features",
                    "Better error handling and validation"
                ]
            },
            {
                "version": "v1",
                "release_date": "2023-01-01",
                "changes": [
                    "Initial release",
                    "Basic CRUD operations",
                    "Authentication and authorization",
                    "Rate limiting"
                ]
            }
        ]
    } 