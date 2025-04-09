from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from app.core.websocket import websocket_manager
from app.core.security import get_current_user
from app.db.session import get_db_session
from sqlalchemy.orm import Session
from typing import Optional


router = APIRouter()


@router.websocket("/ws/vulnerabilities")
async def vulnerability_updates(
    websocket: WebSocket,
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for real-time vulnerability updates.
    """
    await websocket_manager.handle_connection(websocket, "vulnerabilities")


@router.websocket("/ws/notifications")
async def user_notifications(
    websocket: WebSocket,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for user-specific notifications.
    """
    await websocket_manager.handle_connection(
        websocket,
        "notifications",
        current_user.id
    )


@router.websocket("/ws/events")
async def system_events(
    websocket: WebSocket,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for system-wide events.
    """
    await websocket_manager.handle_connection(websocket, "events")


@router.websocket("/ws/chat/{room_id}")
async def chat_room(
    websocket: WebSocket,
    room_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for chat room communication.
    """
    await websocket_manager.handle_connection(websocket, f"chat_{room_id}")


@router.post("/ws/broadcast/{channel}")
async def broadcast_message(
    channel: str,
    message: dict,
    current_user = Depends(get_current_user)
):
    """
    Broadcast a message to all connections in a channel.
    """
    await websocket_manager.broadcast(channel, message)
    return {"status": "message broadcasted"}


@router.post("/ws/user/{user_id}")
async def send_user_message(
    user_id: int,
    message: dict,
    current_user = Depends(get_current_user)
):
    """
    Send a message to a specific user's connections.
    """
    await websocket_manager.send_to_user(user_id, message)
    return {"status": "message sent"} 