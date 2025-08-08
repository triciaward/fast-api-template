import pytest

from app.core.config.config import settings
from app.main import app

pytestmark = pytest.mark.template_only

def test_app_title_matches_settings() -> None:
    assert app.title == settings.PROJECT_NAME


@pytest.mark.asyncio
async def test_features_endpoint(async_client):
    resp = await async_client.get("/features")
    assert resp.status_code == 200
    data = resp.json()
    assert set(["redis", "websockets", "rate_limiting", "celery"]).issubset(data.keys())
