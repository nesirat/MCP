from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import gzip
import zlib
from typing import Optional
from app.core.config import settings


class CompressionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.min_size = settings.COMPRESSION_MIN_SIZE
        self.compression_level = settings.COMPRESSION_LEVEL

    async def dispatch(self, request: Request, call_next):
        # Skip compression if disabled
        if not settings.COMPRESSION_ENABLED:
            return await call_next(request)

        # Get response
        response = await call_next(request)

        # Skip compression for certain content types
        content_type = response.headers.get("content-type", "")
        if any(x in content_type for x in [
            "image/",
            "video/",
            "audio/",
            "application/zip",
            "application/gzip",
            "application/x-gzip",
            "application/x-compress",
            "application/x-bzip2"
        ]):
            return response

        # Skip compression for small responses
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if len(body) < self.min_size:
            return response

        # Get accepted encoding
        accept_encoding = request.headers.get("accept-encoding", "").lower()
        
        # Compress response
        if "gzip" in accept_encoding:
            compressed_body = gzip.compress(body, compresslevel=self.compression_level)
            response.headers["content-encoding"] = "gzip"
        elif "deflate" in accept_encoding:
            compressed_body = zlib.compress(body, level=self.compression_level)
            response.headers["content-encoding"] = "deflate"
        else:
            return response

        # Update response
        response.body = compressed_body
        response.headers["content-length"] = str(len(compressed_body))
        response.headers["vary"] = "accept-encoding"

        return response 