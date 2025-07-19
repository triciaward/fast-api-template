from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_comprehensive_health_check(self, client: TestClient) -> None:
        """Test the comprehensive health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "checks" in data

        # Check checks structure
        checks = data["checks"]
        assert "database" in checks
        assert "application" in checks
        assert checks["application"] == "healthy"

        # Status should be either healthy or unhealthy based on database
        assert data["status"] in ["healthy", "unhealthy"]

        # If database is unhealthy, should have error details
        if data["status"] == "unhealthy":
            assert "database_error" in data

    def test_simple_health_check(self, client: TestClient) -> None:
        """Test the simple health check endpoint."""
        response = client.get("/api/v1/health/simple")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test the readiness check endpoint."""
        response = client.get("/api/v1/health/ready")

        # Should return either 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.json()

        if response.status_code == 200:
            # Check required fields for success
            assert "ready" in data
            assert data["ready"] is True
            assert "timestamp" in data
            assert "components" in data

            # Check components structure
            components = data["components"]
            assert "database" in components
            assert "application" in components
            assert components["application"]["ready"] is True
        else:
            # Check error response structure
            assert "detail" in data
            detail = data["detail"]
            assert detail["ready"] is False
            assert "Service not ready" in detail["message"]
            assert "components" in detail

    def test_liveness_check(self, client: TestClient) -> None:
        """Test the liveness check endpoint."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()

        assert "alive" in data
        assert data["alive"] == "true"
        assert "timestamp" in data

    def test_health_endpoints_are_public(self, client: TestClient) -> None:
        """Test that health endpoints are accessible without authentication."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/simple",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 401 (Unauthorized)
            assert response.status_code != 401

    def test_health_endpoints_response_format(self, client: TestClient) -> None:
        """Test that health endpoints return proper JSON format."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/simple",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 503]  # 503 for readiness failure
            assert "application/json" in response.headers["content-type"]

            # Verify JSON is valid
            data = response.json()
            assert isinstance(data, dict)

    def test_health_endpoints_include_timestamps(self, client: TestClient) -> None:
        """Test that all health endpoints include timestamps."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/simple",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                assert "timestamp" in data
                # Verify timestamp is in ISO format
                assert "T" in data["timestamp"]
                assert (
                    "Z" in data["timestamp"]
                    or "+" in data["timestamp"]
                    or "-" in data["timestamp"]
                )
