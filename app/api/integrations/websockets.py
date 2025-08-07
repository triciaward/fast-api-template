"""
WebSocket demo endpoint for optional WebSocket functionality.

This endpoint demonstrates WebSocket functionality including:
- Connection management
- Echo functionality
- Broadcast messaging
- Room-based messaging
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.middleware.websockets import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/demo")
async def websocket_demo(websocket: WebSocket) -> None:
    """
    WebSocket demo endpoint that handles various message types.

    Message types:
    - "echo": Echo back the message
    - "broadcast": Broadcast message to all clients
    - "room": Join a specific room
    - "room_broadcast": Broadcast to a specific room
    - "status": Get connection status
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                # Try to parse as JSON
                message_data = json.loads(data)
                message_type = message_data.get("type", "echo")
                message_content = message_data.get("message", "")
                room = message_data.get("room", "default")

            except json.JSONDecodeError:
                # If not JSON, treat as simple echo message
                message_type = "echo"
                message_content = data
                room = "default"

            # Handle different message types
            if message_type == "echo":
                # Echo back the message
                response = {
                    "type": "echo",
                    "message": message_content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await manager.send_personal_message(json.dumps(response), websocket)

            elif message_type == "broadcast":
                # Broadcast to all clients
                response = {
                    "type": "broadcast",
                    "message": message_content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sender": "demo",
                }
                await manager.broadcast_json(response)

            elif message_type == "room":
                # Join a specific room
                manager.disconnect(websocket, "default")
                await manager.connect(websocket, room)
                response = {
                    "type": "room_joined",
                    "room": room,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await manager.send_personal_message(json.dumps(response), websocket)

            elif message_type == "room_broadcast":
                # Broadcast to a specific room
                response = {
                    "type": "room_broadcast",
                    "message": message_content,
                    "room": room,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sender": "demo",
                }
                await manager.broadcast_json(response, room)

            elif message_type == "status":
                # Get connection status
                response = {
                    "type": "status",
                    "total_connections": manager.get_total_connections(),
                    "room_connections": manager.get_connection_count(room),
                    "current_room": room,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await manager.send_personal_message(json.dumps(response), websocket)

            else:
                # Unknown message type
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await manager.send_personal_message(json.dumps(response), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
        manager.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status() -> dict[str, Any]:
    """
    Get WebSocket connection status.

    Returns:
        Dictionary with connection statistics
    """
    return {
        "total_connections": manager.get_total_connections(),
        "active_rooms": list(manager.active_connections.keys()),
        "room_connections": {
            room: len(connections)
            for room, connections in manager.active_connections.items()
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
