import pytest

pytestmark = pytest.mark.template_only

@pytest.mark.asyncio
async def test_security_headers_present_on_root(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    headers = resp.headers
    assert "Content-Security-Policy" in headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
