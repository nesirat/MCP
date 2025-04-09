from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime

from app.core.config import settings


class VersionData:
    def __init__(self, version: str, deprecated: bool = False, sunset_date: Optional[datetime] = None):
        self.version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date


class VersioningMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.version_data: Dict[str, VersionData] = {
            "v1": VersionData("v1", deprecated=False),
            "v2": VersionData("v2", deprecated=False),
        }

    async def dispatch(self, request: Request, call_next):
        # Extract version from path
        path = request.url.path
        version = None
        
        for v in self.version_data.keys():
            if f"/api/{v}/" in path:
                version = v
                break
        
        if version:
            version_info = self.version_data.get(version)
            if not version_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"API version {version} not found"
                )
            
            if version_info.deprecated:
                headers = {
                    "Warning": f'299 - "This API version is deprecated"',
                    "X-API-Version": version,
                    "X-API-Deprecated": "true",
                }
                
                if version_info.sunset_date:
                    headers["Sunset"] = version_info.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                
                response = await call_next(request)
                for key, value in headers.items():
                    response.headers[key] = value
                return response
        
        response = await call_next(request)
        if version:
            response.headers["X-API-Version"] = version
        return response

    def deprecate_version(self, version: str, sunset_date: Optional[datetime] = None):
        """Mark an API version as deprecated with an optional sunset date."""
        if version in self.version_data:
            self.version_data[version].deprecated = True
            self.version_data[version].sunset_date = sunset_date 