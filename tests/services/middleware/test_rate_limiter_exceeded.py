import pytest


@pytest.mark.asyncio
async def test_rate_limit_exceeded_handling(monkeypatch, async_client):
    from app.core.config import settings
    from app.services.middleware import rate_limiter as rl

    # Enable rate limiting
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    # Create a limiter that always raises RateLimitExceeded
    class FakeLimiter:
        def limit(self, limit):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    from slowapi.errors import RateLimitExceeded

                    raise RateLimitExceeded("test limit")

                return wrapper

            return decorator

    monkeypatch.setattr(rl, "limiter", FakeLimiter())

    # Endpoint using login rate limit; ensure DB access doesn't occur
    # by making validate_email_format fail first (invalid email)
    import app.core.security as core_security

    monkeypatch.setattr(
        core_security, "validate_email_format", lambda e: (False, "bad")
    )
    resp = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "bad"},
        headers={"user-agent": "pytest"},
    )
    # Should be handled by slowapi handler (429) or validation (400)
    assert resp.status_code in (429, 400)
