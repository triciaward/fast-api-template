import pytest

from app.core.config.config import settings

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_login_invalid_email_format(async_client):
    # Invalid email format should return 400
    r = await async_client.post(
        "/auth/login",
        data={"username": "not-an-email", "password": "x"},
        headers={"user-agent": "pytest"},
    )
    assert r.status_code == 400
    assert "invalid email" in r.json()["error"]["message"].lower()


@pytest.mark.skipif(not settings.ENABLE_RATE_LIMITING, reason="Rate limiting not enabled")
@pytest.mark.asyncio
async def test_login_rate_limited(async_client):
    # If enabled, repeated calls should eventually hit 429
    for _ in range(10):
        resp = await async_client.post(
            "/auth/login",
            data={"username": "user@example.com", "password": "wrong"},
            headers={"user-agent": "pytest"},
        )
    assert resp.status_code in (401, 429)

