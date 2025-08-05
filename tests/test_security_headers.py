"""Tests for Security Headers Middleware."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_security_headers_enabled(client):
    """Test that security headers are added to responses."""
    response = client.get("/")

    # Check that response is successful
    assert response.status_code == 200

    # Check for security headers
    headers = response.headers

    # Content Security Policy
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp

    # X-Content-Type-Options
    assert headers["X-Content-Type-Options"] == "nosniff"

    # X-Frame-Options
    assert headers["X-Frame-Options"] == "DENY"

    # X-XSS-Protection
    assert headers["X-XSS-Protection"] == "1; mode=block"

    # Referrer Policy
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    # Permissions Policy
    assert "Permissions-Policy" in headers
    permissions_policy = headers["Permissions-Policy"]
    assert "camera=()" in permissions_policy
    assert "microphone=()" in permissions_policy
    assert "geolocation=()" in permissions_policy


def test_auth_endpoints_cache_control(client):
    """Test that auth endpoints have proper cache control headers."""
    # Test a non-auth endpoint first
    response = client.get("/")
    assert "Cache-Control" not in response.headers

    # Test an auth endpoint (this should have cache control headers)
    response = client.get("/api/v1/auth/login")
    headers = response.headers

    # Auth endpoints should have cache control headers
    assert "Cache-Control" in headers
    assert "no-store" in headers["Cache-Control"]
    assert "no-cache" in headers["Cache-Control"]
    assert "must-revalidate" in headers["Cache-Control"]
    assert "max-age=0" in headers["Cache-Control"]

    assert "Pragma" in headers
    assert headers["Pragma"] == "no-cache"

    assert "Expires" in headers
    assert headers["Expires"] == "0"


def test_hsts_header_disabled_by_default(client):
    """Test that HSTS header is disabled by default."""
    response = client.get("/")
    headers = response.headers

    # HSTS should not be present by default
    assert "Strict-Transport-Security" not in headers


def test_security_headers_on_api_endpoints(client):
    """Test that security headers are present on API endpoints."""
    response = client.get("/api/v1/health")

    # Check that response is successful
    assert response.status_code == 200

    # Check for security headers
    headers = response.headers

    # Content Security Policy
    assert "Content-Security-Policy" in headers

    # X-Content-Type-Options
    assert headers["X-Content-Type-Options"] == "nosniff"

    # X-Frame-Options
    assert headers["X-Frame-Options"] == "DENY"

    # X-XSS-Protection
    assert headers["X-XSS-Protection"] == "1; mode=block"

    # Referrer Policy
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_security_headers_on_admin_endpoints(client):
    """Test that security headers are present on admin endpoints."""
    response = client.get("/admin/api-keys")

    # Admin endpoints require authentication, so we expect 401
    # But security headers should still be present
    assert response.status_code == 401

    # Check for security headers
    headers = response.headers

    # Content Security Policy
    assert "Content-Security-Policy" in headers

    # X-Content-Type-Options
    assert headers["X-Content-Type-Options"] == "nosniff"

    # X-Frame-Options
    assert headers["X-Frame-Options"] == "DENY"

    # X-XSS-Protection
    assert headers["X-XSS-Protection"] == "1; mode=block"

    # Referrer Policy
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
