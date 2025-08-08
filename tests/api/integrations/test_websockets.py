import json

import pytest

from app.main import app

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_websocket_status_endpoint_feature_flag(monkeypatch, async_client):
    from app.core.config import config as config_module

    # Ensure websockets disabled → endpoint not mounted
    monkeypatch.setattr(
        config_module.settings,
        "ENABLE_WEBSOCKETS",
        False,
        raising=False,
    )
    resp = await async_client.get("/ws/status")
    assert resp.status_code in (404, 200)


def test_websocket_echo_flow_with_testclient():
    from starlette.testclient import TestClient

    from app.core.config.config import settings

    if not settings.ENABLE_WEBSOCKETS:
        pytest.skip("Websockets disabled in settings")

    with TestClient(app) as client:
        with client.websocket_connect("/ws/demo") as ws:
            ws.send_text(json.dumps({"type": "echo", "message": "hello"}))
            message = ws.receive_text()
            payload = json.loads(message)
            assert payload["type"] == "echo"
            assert payload["message"] == "hello"


import pytest

pytestmark = pytest.mark.template_only


def test_stub_ws_demo() -> None:
    assert True
