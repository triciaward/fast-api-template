import types

import pytest

from app.core.config import config as config_module
from app.services.middleware import rate_limiter as rl

pytestmark = pytest.mark.unit


def test_rate_limit_custom_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_RATE_LIMITING", False, raising=False)

    def sample(x: int) -> int:
        return x + 2

    decorated = rl.rate_limit_custom("2/minute")(sample)
    assert decorated is sample


@pytest.mark.asyncio
async def test_init_rate_limiter_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_RATE_LIMITING", False, raising=False)
    # Should not raise and not create limiter
    rl.limiter = None
    await rl.init_rate_limiter()
    assert rl.limiter is None


def test_get_rate_limit_info_error_path(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_RATE_LIMITING", True, raising=False)

    class BadRequest:
        def __init__(self):
            self.headers = {}
            self.client = types.SimpleNamespace(host="1.2.3.4")

    # Force get_client_ip to raise
    monkeypatch.setattr(rl, "get_client_ip", lambda req: (_ for _ in ()).throw(RuntimeError("boom")))

    info = rl.get_rate_limit_info(BadRequest())  # type: ignore[arg-type]
    assert info["enabled"] is True
    assert info["error"].startswith("Failed")
