"""
WebSocket connection manager for optional WebSocket functionality.

This module provides WebSocket connection management that is only loaded when ENABLE_WEBSOCKETS=true.
Supports multiple client connections with broadcast functionality.
"""

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for broadcasting messages to multiple clients.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str = "default") -> None:
        """
        Accept a new WebSocket connection and add it to the specified room.

        Args:
            websocket: The WebSocket connection to accept
            room: The room/channel to add the connection to
        """
        await websocket.accept()

        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)
        logger.info(
            f"WebSocket connected to room '{room}'. Total connections: {len(self.active_connections[room])}",
        )

    def disconnect(self, websocket: WebSocket, room: str = "default") -> None:
        """
        Remove a WebSocket connection from the specified room.

        Args:
            websocket: The WebSocket connection to remove
            room: The room/channel to remove the connection from
        """
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)

            # Remove empty rooms
            if not self.active_connections[room]:
                del self.active_connections[room]

            logger.info(f"WebSocket disconnected from room '{room}'")

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: The message to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_text(message)
        except Exception:
            logger.exception("Error sending personal message")

    async def broadcast(self, message: str, room: str = "default") -> None:
        """
        Broadcast a message to all connections in a specific room.

        Args:
            message: The message to broadcast
            room: The room/channel to broadcast to
        """
        if room not in self.active_connections:
            return

        disconnected_websockets = set()

        for connection in self.active_connections[room]:
            try:
                await connection.send_text(message)
            except Exception:
                logger.exception("Error broadcasting message")
                disconnected_websockets.add(connection)

        # Remove disconnected websockets
        for connection in disconnected_websockets:
            self.disconnect(connection, room)

    async def broadcast_json(self, data: dict, room: str = "default") -> None:
        """
        Broadcast a JSON message to all connections in a specific room.

        Args:
            data: The data to broadcast as JSON
            room: The room/channel to broadcast to
        """
        message = json.dumps(data)
        await self.broadcast(message, room)

    def get_connection_count(self, room: str = "default") -> int:
        """
        Get the number of active connections in a room.

        Args:
            room: The room to count connections for

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(room, set()))

    def get_total_connections(self) -> int:
        """
        Get the total number of active connections across all rooms.

        Returns:
            Total number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()
