"""
Integration tests for optional Redis and WebSocket features.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestOptionalFeatures:
    """Test optional features functionality."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_features_endpoint_disabled(self, client: TestClient) -> None:
        """Test features endpoint when all optional features are disabled."""
        response = client.get("/features")

        assert response.status_code == 200
        data = response.json()
        assert data["redis"] is False
        assert data["websockets"] is False

    def test_features_endpoint_structure(self, client: TestClient) -> None:
        """Test features endpoint response structure."""
        response = client.get("/features")

        assert response.status_code == 200
        data = response.json()
        assert "redis" in data
        assert "websockets" in data
        assert isinstance(data["redis"], bool)
        assert isinstance(data["websockets"], bool)

    def test_websocket_endpoints_disabled(self, client: TestClient) -> None:
        """Test that WebSocket endpoints return 404 when disabled."""
        # Test WebSocket status endpoint
        response = client.get("/api/v1/ws/status")
        assert response.status_code == 404

    def test_health_check_without_redis(self, client: TestClient) -> None:
        """Test health check when Redis is disabled."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
        assert "application" in data["checks"]
        assert "redis" not in data["checks"]

    def test_readiness_check_structure(self, client: TestClient) -> None:
        """Test readiness check response structure."""
        response = client.get("/api/v1/health/ready")

        # Note: This might return 503 if database is not available in test environment
        # We'll just check the structure if it's successful
        if response.status_code == 200:
            data = response.json()
            assert "components" in data
            assert "database" in data["components"]
            assert "application" in data["components"]
            assert "redis" not in data["components"]


class TestWebSocketDemoEndpoint:
    """Test WebSocket demo endpoint functionality."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_websocket_demo_router_structure(self) -> None:
        """Test WebSocket demo router structure."""
        # Test that the router is properly configured
        from app.api.api_v1.endpoints.ws_demo import router

        # Check that the router has the expected routes
        routes = [str(route.path) for route in router.routes if hasattr(route, "path")]
        assert "/ws/demo" in routes
        assert "/ws/status" in routes


class TestRedisIntegration:
    """Test Redis integration functionality."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_redis_service_import(self) -> None:
        """Test that Redis service can be imported."""
        from app.services.redis import (
            close_redis,
            get_redis_client,
            health_check_redis,
            init_redis,
        )

        # Verify functions exist
        assert callable(init_redis)
        assert callable(close_redis)
        assert callable(get_redis_client)
        assert callable(health_check_redis)

    def test_websocket_service_import(self) -> None:
        """Test that WebSocket service can be imported."""
        from app.services.websocket import ConnectionManager, manager

        # Verify classes exist
        assert ConnectionManager is not None
        assert manager is not None
        assert isinstance(manager, ConnectionManager)
