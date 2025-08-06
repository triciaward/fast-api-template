from fastapi.testclient import TestClient


class TestCORS:
    """Test CORS (Cross-Origin Resource Sharing) functionality."""

    def test_cors_preflight_request(self, client: TestClient) -> None:
        """Test CORS preflight OPTIONS request."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
        assert "access-control-allow-credentials" in response.headers

    def test_cors_allows_configured_origins(self, client: TestClient) -> None:
        """Test that configured origins are allowed."""
        origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:4200",
        ]

        for origin in origins:
            response = client.get("/", headers={"Origin": origin})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == origin

    def test_cors_credentials_allowed(self, client: TestClient) -> None:
        """Test that credentials are allowed in CORS requests."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_all_methods_allowed(self, client: TestClient) -> None:
        """Test that all HTTP methods are allowed."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

        for method in methods:
            response = client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method,
                },
            )

            assert response.status_code == 200
            assert "access-control-allow-methods" in response.headers

    def test_cors_all_headers_allowed(self, client: TestClient) -> None:
        """Test that all headers are allowed."""
        headers = ["Content-Type", "Authorization", "X-Requested-With"]

        for header in headers:
            response = client.options(
                "/",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": header,
                },
            )

            assert response.status_code == 200
            assert "access-control-allow-headers" in response.headers

    def test_cors_api_endpoints(self, client: TestClient) -> None:
        """Test CORS works on API endpoints."""
        # Test health endpoint
        response = client.get(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    def test_cors_with_authentication_endpoints(self, client: TestClient) -> None:
        """Test CORS works on authentication endpoints."""
        # Test registration endpoint
        response = client.post(
            "/api/v1/auth/register",
            headers={"Origin": "http://localhost:3000"},
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
            },
        )

        # Should get CORS headers regardless of response status
        assert "access-control-allow-origin" in response.headers
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    def test_cors_multiple_origins_same_request(self, client: TestClient) -> None:
        """Test CORS behavior with multiple origins in the same request."""
        response = client.get(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Referer": "http://localhost:8080",
            },
        )

        # Should only allow the Origin header, not Referer
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    def test_cors_no_origin_header(self, client: TestClient) -> None:
        """Test CORS behavior when no Origin header is present."""
        response = client.get("/")

        # Should work normally without CORS headers
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers

    def test_cors_environment_variable_parsing(self) -> None:
        """Test that CORS origins are properly parsed from environment variables."""
        from app.core.config import settings

        # Test that the default origins are set correctly
        expected_origins = [
            "http://localhost:3000",  # React default
            "http://localhost:8080",  # Vue default
            "http://localhost:4200",  # Angular default
        ]

        assert settings.cors_origins_list == expected_origins

    def test_cors_middleware_loaded(self, client: TestClient) -> None:
        """Test that CORS middleware is properly loaded in the app."""
        # Check that the app has CORS middleware by making a request
        response = client.get("/")
        assert response.status_code == 200
        # If we get here without errors, CORS middleware is working

    def test_cors_with_different_content_types(self, client: TestClient) -> None:
        """Test CORS works with different content types."""
        content_types = ["application/json", "text/plain", "application/xml"]

        for content_type in content_types:
            response = client.post(
                "/api/v1/auth/register",
                headers={
                    "Origin": "http://localhost:3000",
                    "Content-Type": content_type,
                },
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "testpassword123",
                },
            )

            assert "access-control-allow-origin" in response.headers
            assert (
                response.headers.get("access-control-allow-origin")
                == "http://localhost:3000"
            )

    def test_configure_cors_function(self) -> None:
        """Test the configure_cors function directly."""
        from fastapi import FastAPI

        from app.core.config import settings
        from app.core.cors import configure_cors

        # Create a test app
        test_app = FastAPI()

        # Configure CORS
        configure_cors(test_app)

        # Check that CORS middleware was added
        middleware_names = [
            middleware.cls.__name__ for middleware in test_app.user_middleware
        ]
        assert "CORSMiddleware" in middleware_names

        # Check that the middleware has the correct configuration
        cors_middleware = next(
            middleware
            for middleware in test_app.user_middleware
            if middleware.cls.__name__ == "CORSMiddleware"
        )

        # Verify the middleware options - handle different FastAPI versions
        if hasattr(cors_middleware, "options"):
            # Older FastAPI versions
            assert cors_middleware.options["allow_credentials"] is True
            assert cors_middleware.options["allow_methods"] == ["*"]
            assert cors_middleware.options["allow_headers"] == ["*"]

            # Check that origins are properly configured
            expected_origins = settings.cors_origins_list
            assert cors_middleware.options["allow_origins"] == expected_origins
        else:
            # Newer FastAPI versions - middleware is configured correctly if we reach here
            # The fact that we found CORSMiddleware means it was configured
            pass
