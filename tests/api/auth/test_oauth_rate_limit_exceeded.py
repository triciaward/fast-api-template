import pytest


@pytest.mark.asyncio
async def test_oauth_rate_limit_exceeded(monkeypatch, async_client):
    from app.core.config import settings
    from app.main import app
    from app.services.middleware import rate_limiter as rl

    # Skip if limiter wasn't configured at startup
    if not getattr(app.state, "limiter", None):
        pytest.skip("Rate limiting not configured at app startup")

    monkeypatch.setattr(settings, "ENABLE_RATE_LIMITING", True)

    class FakeLimiter:
        def limit(self, limit):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    from slowapi.errors import RateLimitExceeded

                    raise RateLimitExceeded("oauth limit")

                return wrapper

            return decorator

    monkeypatch.setattr(rl, "limiter", FakeLimiter())

    resp = await async_client.post(
        "/api/auth/oauth/login",
        json={"provider": "google", "access_token": "token"},
        headers={"user-agent": "pytest"},
    )
    assert resp.status_code in (429,)
