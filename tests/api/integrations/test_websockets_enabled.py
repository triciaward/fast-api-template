import pytest


def test_websocket_echo_when_enabled(monkeypatch):
    from starlette.testclient import TestClient

    from app.core.config import settings
    from app.main import app

    if not settings.ENABLE_WEBSOCKETS:
        pytest.skip("Websockets not enabled")

    with TestClient(app) as client:
        with client.websocket_connect("/ws/demo") as ws:
            ws.send_json({"type": "echo", "message": "hello"})
            msg = ws.receive_json()
            assert msg["type"] == "echo"
            assert msg["message"] == "hello"


def test_websocket_room_and_broadcast_when_enabled():
    from starlette.testclient import TestClient

    from app.core.config import settings
    from app.main import app

    if not settings.ENABLE_WEBSOCKETS:
        pytest.skip("Websockets not enabled")

    with TestClient(app) as client:
        with (
            client.websocket_connect("/ws/demo") as ws1,
            client.websocket_connect("/ws/demo") as ws2,
        ):
            ws1.send_json({"type": "room", "room": "r1"})
            _ = ws1.receive_json()
            ws2.send_json({"type": "room", "room": "r1"})
            _ = ws2.receive_json()

            ws1.send_json({"type": "room_broadcast", "room": "r1", "message": "ping"})
            rcv1 = ws1.receive_json()
            rcv2 = ws2.receive_json()
            assert rcv1["type"] == "room_broadcast" and rcv1["message"] == "ping"
            assert rcv2["type"] == "room_broadcast" and rcv2["message"] == "ping"


def test_websocket_status_endpoint_when_enabled():
    from starlette.testclient import TestClient

    from app.core.config import settings
    from app.main import app

    if not settings.ENABLE_WEBSOCKETS:
        pytest.skip("Websockets not enabled")

    with TestClient(app) as client:
        resp = client.get("/ws/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_connections" in data and "active_rooms" in data
