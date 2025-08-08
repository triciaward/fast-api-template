import pytest


@pytest.mark.asyncio
async def test_password_reset_rate_limit_exceeded(monkeypatch, async_client):
    from app.core.config import settings
    from app.main import app
    from app.services.middleware import rate_limiter as rl

    if not getattr(app.state, "limiter", None):
        pytest.skip("Rate limiting not configured at app startup")

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    class FakeLimiter:
        def limit(self, limit):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    from slowapi.errors import RateLimitExceeded

                    raise RateLimitExceeded("pw reset limit")

                return wrapper

            return decorator

    monkeypatch.setattr(rl, "limiter", FakeLimiter())

    resp = await async_client.post(
        "/auth/forgot-password",
        json={"email": "user@example.com"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code in (429,)


