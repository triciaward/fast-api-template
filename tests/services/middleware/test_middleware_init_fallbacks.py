import importlib
import sys
import types

import pytest


@pytest.mark.unit
def test_rate_limiter_importerror_fallback(monkeypatch):
    # Ensure a clean re-import of the package module with a stubbed submodule
    module_name = "app.services.middleware"
    submodule_name = "app.services.middleware.rate_limiter"

    # Provide an empty rate_limiter module so attribute imports fail -> ImportError
    stub = types.ModuleType(submodule_name)
    monkeypatch.setitem(sys.modules, submodule_name, stub)
    # Remove the main module so it re-imports with the stubbed submodule
    sys.modules.pop(module_name, None)

    mod = importlib.import_module(module_name)

    # rate limiter symbols should fallback to no-ops / defaults
    def f(x):
        return x + 1

    assert mod.rate_limit_custom("1/minute")(f) is f
    assert mod.get_rate_limit_info(types.SimpleNamespace()) == {"enabled": False}
    assert mod.get_client_ip(types.SimpleNamespace()) == "unknown"


@pytest.mark.unit
def test_websockets_importerror_fallback(monkeypatch):
    module_name = "app.services.middleware"
    submodule_name = "app.services.middleware.websockets"

    # Provide an empty websockets module so attribute import fails -> ImportError
    stub = types.ModuleType(submodule_name)
    monkeypatch.setitem(sys.modules, submodule_name, stub)
    sys.modules.pop(module_name, None)

    mod = importlib.import_module(module_name)

    # Fallback should expose None values
    assert getattr(mod, "ConnectionManager", None) is None
    assert getattr(mod, "websocket_manager", None) is None
