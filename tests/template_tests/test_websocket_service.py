"""
Tests for WebSocket service.

This module tests the WebSocket connection manager functionality including connection management, messaging, and broadcasting.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import WebSocket

from app.services.websocket import ConnectionManager, manager


class TestConnectionManagerInitialization:
    """Test ConnectionManager initialization."""

    def test_connection_manager_initialization(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager()
        assert manager.active_connections == {}


class TestConnectionManagement:
    """Test WebSocket connection management."""

    async def test_connect_new_room(self):
        """Test connecting to a new room."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)

        await manager.connect(mock_websocket, "test_room")

        assert "test_room" in manager.active_connections
        assert mock_websocket in manager.active_connections["test_room"]
        assert len(manager.active_connections["test_room"]) == 1
        mock_websocket.accept.assert_called_once()

    async def test_connect_existing_room(self):
        """Test connecting to an existing room."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)

        # Connect first websocket
        await manager.connect(mock_websocket1, "test_room")

        # Connect second websocket to same room
        await manager.connect(mock_websocket2, "test_room")

        assert "test_room" in manager.active_connections
        assert mock_websocket1 in manager.active_connections["test_room"]
        assert mock_websocket2 in manager.active_connections["test_room"]
        assert len(manager.active_connections["test_room"]) == 2

    async def test_connect_default_room(self):
        """Test connecting to default room."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)

        await manager.connect(mock_websocket)

        assert "default" in manager.active_connections
        assert mock_websocket in manager.active_connections["default"]
        mock_websocket.accept.assert_called_once()

    def test_disconnect_existing_connection(self):
        """Test disconnecting an existing connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["test_room"] = {mock_websocket}

        manager.disconnect(mock_websocket, "test_room")

        assert "test_room" not in manager.active_connections

    def test_disconnect_nonexistent_room(self):
        """Test disconnecting from a non-existent room."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)

        # Should not raise an exception
        manager.disconnect(mock_websocket, "nonexistent_room")

    def test_disconnect_remove_empty_room(self):
        """Test that empty rooms are removed after disconnection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["test_room"] = {mock_websocket}

        manager.disconnect(mock_websocket, "test_room")

        assert "test_room" not in manager.active_connections

    def test_disconnect_partial_room(self):
        """Test disconnecting one connection from a room with multiple connections."""
        manager = ConnectionManager()
        mock_websocket1 = MagicMock(spec=WebSocket)
        mock_websocket2 = MagicMock(spec=WebSocket)

        # Add connections manually
        manager.active_connections["test_room"] = {mock_websocket1, mock_websocket2}

        manager.disconnect(mock_websocket1, "test_room")

        assert "test_room" in manager.active_connections
        assert mock_websocket2 in manager.active_connections["test_room"]
        assert mock_websocket1 not in manager.active_connections["test_room"]
        assert len(manager.active_connections["test_room"]) == 1


class TestPersonalMessaging:
    """Test personal message functionality."""

    async def test_send_personal_message_success(self):
        """Test successful personal message sending."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)

        await manager.send_personal_message("Hello, World!", mock_websocket)

        mock_websocket.send_text.assert_called_once_with("Hello, World!")

    async def test_send_personal_message_error(self):
        """Test personal message sending with error."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.send_text.side_effect = Exception("Connection lost")

        # Should not raise an exception, just log the error
        await manager.send_personal_message("Hello, World!", mock_websocket)

        mock_websocket.send_text.assert_called_once_with("Hello, World!")


class TestBroadcasting:
    """Test broadcasting functionality."""

    async def test_broadcast_to_empty_room(self):
        """Test broadcasting to an empty room."""
        manager = ConnectionManager()

        # Should not raise an exception
        await manager.broadcast("Hello, World!", "empty_room")

    async def test_broadcast_to_single_connection(self):
        """Test broadcasting to a room with one connection."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["test_room"] = {mock_websocket}

        await manager.broadcast("Hello, World!", "test_room")

        mock_websocket.send_text.assert_called_once_with("Hello, World!")

    async def test_broadcast_to_multiple_connections(self):
        """Test broadcasting to a room with multiple connections."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)

        # Add connections manually
        manager.active_connections["test_room"] = {mock_websocket1, mock_websocket2}

        await manager.broadcast("Hello, World!", "test_room")

        mock_websocket1.send_text.assert_called_once_with("Hello, World!")
        mock_websocket2.send_text.assert_called_once_with("Hello, World!")

    async def test_broadcast_with_connection_error(self):
        """Test broadcasting with connection error."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket1.send_text.side_effect = Exception("Connection lost")

        # Add connections manually
        manager.active_connections["test_room"] = {mock_websocket1, mock_websocket2}

        await manager.broadcast("Hello, World!", "test_room")

        # First connection should fail, second should succeed
        mock_websocket1.send_text.assert_called_once_with("Hello, World!")
        mock_websocket2.send_text.assert_called_once_with("Hello, World!")

        # Failed connection should be removed
        assert mock_websocket1 not in manager.active_connections["test_room"]
        assert mock_websocket2 in manager.active_connections["test_room"]

    async def test_broadcast_json_success(self):
        """Test successful JSON broadcasting."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["test_room"] = {mock_websocket}

        test_data = {"message": "Hello", "user": "test_user", "timestamp": "2023-01-01"}

        await manager.broadcast_json(test_data, "test_room")

        expected_json = json.dumps(test_data)
        mock_websocket.send_text.assert_called_once_with(expected_json)

    async def test_broadcast_json_empty_room(self):
        """Test JSON broadcasting to empty room."""
        manager = ConnectionManager()

        test_data = {"message": "Hello", "user": "test_user"}

        # Should not raise an exception
        await manager.broadcast_json(test_data, "empty_room")


class TestConnectionCounting:
    """Test connection counting functionality."""

    def test_get_connection_count_empty_room(self):
        """Test getting connection count for empty room."""
        manager = ConnectionManager()

        count = manager.get_connection_count("empty_room")
        assert count == 0

    def test_get_connection_count_single_connection(self):
        """Test getting connection count for room with one connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["test_room"] = {mock_websocket}

        count = manager.get_connection_count("test_room")
        assert count == 1

    def test_get_connection_count_multiple_connections(self):
        """Test getting connection count for room with multiple connections."""
        manager = ConnectionManager()
        mock_websocket1 = MagicMock(spec=WebSocket)
        mock_websocket2 = MagicMock(spec=WebSocket)
        mock_websocket3 = MagicMock(spec=WebSocket)

        # Add connections manually
        manager.active_connections["test_room"] = {
            mock_websocket1,
            mock_websocket2,
            mock_websocket3,
        }

        count = manager.get_connection_count("test_room")
        assert count == 3

    def test_get_connection_count_default_room(self):
        """Test getting connection count for default room."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)

        # Add connection manually
        manager.active_connections["default"] = {mock_websocket}

        count = manager.get_connection_count()
        assert count == 1

    def test_get_total_connections_empty(self):
        """Test getting total connections when no connections exist."""
        manager = ConnectionManager()

        total = manager.get_total_connections()
        assert total == 0

    def test_get_total_connections_single_room(self):
        """Test getting total connections for single room."""
        manager = ConnectionManager()
        mock_websocket1 = MagicMock(spec=WebSocket)
        mock_websocket2 = MagicMock(spec=WebSocket)

        # Add connections manually
        manager.active_connections["test_room"] = {mock_websocket1, mock_websocket2}

        total = manager.get_total_connections()
        assert total == 2

    def test_get_total_connections_multiple_rooms(self):
        """Test getting total connections across multiple rooms."""
        manager = ConnectionManager()
        mock_websocket1 = MagicMock(spec=WebSocket)
        mock_websocket2 = MagicMock(spec=WebSocket)
        mock_websocket3 = MagicMock(spec=WebSocket)
        mock_websocket4 = MagicMock(spec=WebSocket)

        # Add connections to multiple rooms
        manager.active_connections["room1"] = {mock_websocket1, mock_websocket2}
        manager.active_connections["room2"] = {mock_websocket3, mock_websocket4}

        total = manager.get_total_connections()
        assert total == 4


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios."""

    async def test_complete_websocket_lifecycle(self):
        """Test complete WebSocket lifecycle."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)

        # Step 1: Connect two websockets
        await manager.connect(mock_websocket1, "test_room")
        await manager.connect(mock_websocket2, "test_room")

        assert manager.get_connection_count("test_room") == 2
        assert manager.get_total_connections() == 2

        # Step 2: Send personal message
        await manager.send_personal_message("Personal message", mock_websocket1)
        mock_websocket1.send_text.assert_called_once_with("Personal message")

        # Step 3: Broadcast message
        await manager.broadcast("Broadcast message", "test_room")
        mock_websocket1.send_text.assert_called_with("Broadcast message")
        mock_websocket2.send_text.assert_called_once_with("Broadcast message")

        # Step 4: Broadcast JSON
        test_data = {"type": "notification", "message": "JSON broadcast"}
        await manager.broadcast_json(test_data, "test_room")
        expected_json = json.dumps(test_data)
        mock_websocket1.send_text.assert_called_with(expected_json)
        mock_websocket2.send_text.assert_called_with(expected_json)

        # Step 5: Disconnect one websocket
        manager.disconnect(mock_websocket1, "test_room")
        assert manager.get_connection_count("test_room") == 1
        assert manager.get_total_connections() == 1

        # Step 6: Disconnect remaining websocket
        manager.disconnect(mock_websocket2, "test_room")
        assert manager.get_connection_count("test_room") == 0
        assert manager.get_total_connections() == 0
        assert "test_room" not in manager.active_connections

    async def test_multiple_rooms_management(self):
        """Test managing multiple rooms."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket3 = AsyncMock(spec=WebSocket)

        # Connect to different rooms
        await manager.connect(mock_websocket1, "room1")
        await manager.connect(mock_websocket2, "room2")
        await manager.connect(mock_websocket3, "room1")

        assert manager.get_connection_count("room1") == 2
        assert manager.get_connection_count("room2") == 1
        assert manager.get_total_connections() == 3

        # Broadcast to specific room
        await manager.broadcast("Room1 message", "room1")
        mock_websocket1.send_text.assert_called_once_with("Room1 message")
        mock_websocket3.send_text.assert_called_once_with("Room1 message")
        mock_websocket2.send_text.assert_not_called()

        # Broadcast to other room
        await manager.broadcast("Room2 message", "room2")
        mock_websocket2.send_text.assert_called_once_with("Room2 message")

    async def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        manager = ConnectionManager()
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        mock_websocket1.send_text.side_effect = Exception("Connection lost")

        # Connect websockets
        await manager.connect(mock_websocket1, "test_room")
        await manager.connect(mock_websocket2, "test_room")

        # Broadcast should handle the error gracefully
        await manager.broadcast("Test message", "test_room")

        # Failed connection should be removed
        assert mock_websocket1 not in manager.active_connections["test_room"]
        assert mock_websocket2 in manager.active_connections["test_room"]
        assert manager.get_connection_count("test_room") == 1


class TestGlobalManager:
    """Test the global manager instance."""

    def test_global_manager_instance(self):
        """Test that the global manager is properly initialized."""
        assert isinstance(manager, ConnectionManager)
        assert manager.active_connections == {}

    async def test_global_manager_functionality(self):
        """Test that the global manager works correctly."""
        mock_websocket = AsyncMock(spec=WebSocket)

        # Test global manager
        await manager.connect(mock_websocket, "global_test")
        assert manager.get_connection_count("global_test") == 1

        await manager.send_personal_message("Global test", mock_websocket)
        mock_websocket.send_text.assert_called_once_with("Global test")

        manager.disconnect(mock_websocket, "global_test")
        assert manager.get_connection_count("global_test") == 0
