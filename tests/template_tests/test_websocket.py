"""
Unit tests for WebSocket service module.
"""

import json
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.services.websocket import ConnectionManager, manager


class TestConnectionManager:
    """Test WebSocket connection manager functionality."""

    @pytest.fixture
    def connection_manager(self) -> ConnectionManager:
        """Create a fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self) -> AsyncMock:
        """Create a mock WebSocket connection."""
        websocket = AsyncMock(spec=WebSocket)
        return websocket

    @pytest.mark.asyncio
    async def test_connect_new_room(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test connecting to a new room."""
        await connection_manager.connect(mock_websocket, "test-room")

        assert "test-room" in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections["test-room"]
        assert len(connection_manager.active_connections["test-room"]) == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_existing_room(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test connecting to an existing room."""
        # Add first connection
        await connection_manager.connect(mock_websocket, "test-room")

        # Add second connection
        mock_websocket2 = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket2, "test-room")

        assert len(connection_manager.active_connections["test-room"]) == 2
        assert mock_websocket in connection_manager.active_connections["test-room"]
        assert mock_websocket2 in connection_manager.active_connections["test-room"]

    @pytest.mark.asyncio
    async def test_connect_default_room(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test connecting to default room."""
        await connection_manager.connect(mock_websocket)

        assert "default" in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections["default"]

    def test_disconnect_existing_connection(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test disconnecting an existing connection."""
        # Setup: add connection
        connection_manager.active_connections["test-room"] = {mock_websocket}

        connection_manager.disconnect(mock_websocket, "test-room")

        assert "test-room" not in connection_manager.active_connections

    def test_disconnect_nonexistent_room(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test disconnecting from a room that doesn't exist."""
        connection_manager.disconnect(mock_websocket, "nonexistent-room")
        # Should not raise any exceptions

    def test_disconnect_remove_empty_room(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test that empty rooms are removed after disconnection."""
        # Setup: add connection
        connection_manager.active_connections["test-room"] = {mock_websocket}

        connection_manager.disconnect(mock_websocket, "test-room")

        assert "test-room" not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message_success(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test sending a personal message successfully."""
        message = "Hello, World!"

        await connection_manager.send_personal_message(message, mock_websocket)

        mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_error(
        self, connection_manager: ConnectionManager, mock_websocket: AsyncMock
    ) -> None:
        """Test sending a personal message with error."""
        message = "Hello, World!"
        mock_websocket.send_text.side_effect = Exception("Send failed")

        await connection_manager.send_personal_message(message, mock_websocket)
        # Should not raise exception

    @pytest.mark.asyncio
    async def test_broadcast_empty_room(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcasting to an empty room."""
        message = "Hello, World!"

        await connection_manager.broadcast(message, "empty-room")
        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_broadcast_success(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test successful broadcast to room."""
        message = "Hello, World!"
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)

        # Setup connections
        connection_manager.active_connections["test-room"] = {
            mock_websocket1,
            mock_websocket2,
        }

        await connection_manager.broadcast(message, "test-room")

        mock_websocket1.send_text.assert_called_once_with(message)
        mock_websocket2.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_websocket(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test broadcast that removes disconnected websockets."""
        message = "Hello, World!"
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket2.send_text.side_effect = Exception("Connection lost")

        # Setup connections
        connection_manager.active_connections["test-room"] = {
            mock_websocket1,
            mock_websocket2,
        }

        await connection_manager.broadcast(message, "test-room")

        # First websocket should receive message
        mock_websocket1.send_text.assert_called_once_with(message)
        # Second websocket should be removed due to error, but first one remains
        assert "test-room" in connection_manager.active_connections
        assert mock_websocket1 in connection_manager.active_connections["test-room"]
        assert mock_websocket2 not in connection_manager.active_connections["test-room"]

    @pytest.mark.asyncio
    async def test_broadcast_json(self, connection_manager: ConnectionManager) -> None:
        """Test broadcasting JSON data."""
        data = {"type": "message", "content": "Hello"}
        mock_websocket = AsyncMock(spec=WebSocket)

        # Setup connection
        connection_manager.active_connections["test-room"] = {mock_websocket}

        await connection_manager.broadcast_json(data, "test-room")

        expected_message = json.dumps(data)
        mock_websocket.send_text.assert_called_once_with(expected_message)

    def test_get_connection_count_empty_room(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test getting connection count for empty room."""
        count = connection_manager.get_connection_count("empty-room")
        assert count == 0

    def test_get_connection_count_existing_room(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test getting connection count for room with connections."""
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)

        connection_manager.active_connections["test-room"] = {
            mock_websocket1,
            mock_websocket2,
        }

        count = connection_manager.get_connection_count("test-room")
        assert count == 2

    def test_get_total_connections_empty(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test getting total connections when none exist."""
        total = connection_manager.get_total_connections()
        assert total == 0

    def test_get_total_connections_multiple_rooms(
        self, connection_manager: ConnectionManager
    ) -> None:
        """Test getting total connections across multiple rooms."""
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        connection_manager.active_connections["room1"] = {
            mock_websocket1,
            mock_websocket2,
        }
        connection_manager.active_connections["room2"] = {mock_websocket3}

        total = connection_manager.get_total_connections()
        assert total == 3


class TestGlobalManager:
    """Test the global connection manager instance."""

    def test_global_manager_instance(self) -> None:
        """Test that global manager is properly instantiated."""
        assert isinstance(manager, ConnectionManager)
        assert hasattr(manager, "active_connections")
        assert isinstance(manager.active_connections, dict)
