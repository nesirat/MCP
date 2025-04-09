from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import List, Optional
from app.core.config import settings


class HTTP2Middleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.push_paths = {
            "/": [
                "/static/css/main.css",
                "/static/js/main.js",
                "/static/images/logo.png"
            ],
            "/api/v1/docs": [
                "/static/css/swagger.css",
                "/static/js/swagger.js"
            ]
        }

    async def dispatch(self, request: Request, call_next):
        # Get response
        response = await call_next(request)

        # Add HTTP/2 headers
        response.headers["x-http2-enabled"] = "true"
        
        # Check if server push is supported
        if "h2" in request.headers.get("upgrade", "").lower():
            # Get paths to push based on current path
            current_path = request.url.path
            paths_to_push = self.push_paths.get(current_path, [])

            # Add Link headers for server push
            if paths_to_push:
                link_headers = []
                for path in paths_to_push:
                    link_headers.append(f"<{path}>; rel=preload")
                response.headers["link"] = ", ".join(link_headers)

        return response 