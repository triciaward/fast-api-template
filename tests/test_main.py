from fastapi.testclient import TestClient


class TestMainApp:
    """Test main FastAPI application endpoints."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "FastAPI Template is running!" in data["message"]

    def test_health_check_endpoint_moved_to_api(self, client: TestClient) -> None:
        """Test that health check endpoint is now available via API."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_openapi_docs_accessible(self, client: TestClient) -> None:
        """Test that OpenAPI documentation is accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        # Should return HTML content for Swagger UI
        assert "text/html" in response.headers["content-type"]

    def test_redoc_docs_accessible(self, client: TestClient) -> None:
        """Test that ReDoc documentation is accessible."""
        response = client.get("/redoc")

        assert response.status_code == 200
        # Should return HTML content for ReDoc
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_accessible(self, client: TestClient) -> None:
        """Test that OpenAPI JSON schema is accessible."""
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        # Should return JSON content
        assert "application/json" in response.headers["content-type"]

        data = response.json()
        # Should contain OpenAPI schema information
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_cors_headers(self, client: TestClient) -> None:
        """Test that CORS headers are properly set."""
        # Test preflight request
        response = client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should allow the request
        assert response.status_code == 200

    def test_nonexistent_endpoint(self, client: TestClient) -> None:
        """Test accessing a non-existent endpoint."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found" in data["detail"]


class TestAPIVersioning:
    """Test API versioning and routing."""

    def test_api_v1_prefix(self, client: TestClient) -> None:
        """Test that API endpoints are properly prefixed with /api/v1."""
        # Test auth endpoints
        response = client.get("/api/v1/auth/register")
        # Should return 405 Method Not Allowed (GET not allowed, only POST)
        assert response.status_code == 405

        # Test users endpoint (should require authentication)
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401  # Unauthorized

    def test_endpoints_without_prefix_not_found(self, client: TestClient) -> None:
        """Test that endpoints without API prefix return 404."""
        # These should not exist without the /api/v1 prefix
        response = client.post("/auth/register")
        assert response.status_code == 404

        response = client.get("/users/me")
        assert response.status_code == 404
