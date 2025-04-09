from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    vulnerabilities,
    health,
    websocket
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["vulnerabilities"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"]) 