import types

import pytest

from app.core.config import config as config_module
from app.services.middleware import rate_limiter as rl

pytestmark = pytest.mark.unit


def test_rate_limit_decorators_noop_when_disabled(monkeypatch) -> None:
    # Force rate limiting disabled
    monkeypatch.setattr(
        config_module.settings,
        "ENABLE_RATE_LIMITING",
        False,
        raising=False,
    )

    def sample(x: int) -> int:
        return x + 1

    assert rl.rate_limit_login(sample) is sample
    assert rl.rate_limit_register(sample) is sample
    assert rl.rate_limit_oauth(sample) is sample
    assert rl.rate_limit_password_reset(sample) is sample
    assert rl.rate_limit_account_deletion(sample) is sample
    assert rl.rate_limit_custom("1/minute")(sample) is sample


def test_get_rate_limit_info_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        config_module.settings,
        "ENABLE_RATE_LIMITING",
        False,
        raising=False,
    )

    request = types.SimpleNamespace(
        headers={},
        client=types.SimpleNamespace(host="127.0.0.1"),
    )
    info = rl.get_rate_limit_info(request)  # type: ignore[arg-type]
    assert info == {"enabled": False}
