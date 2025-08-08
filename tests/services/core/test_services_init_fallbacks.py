import importlib
import sys
import types

import pytest


@pytest.mark.unit
def test_services_celery_import_fallback(monkeypatch):
    module_name = "app.services"
    submodule_name = "app.services.background"

    # Provide an empty background module to trigger ImportError on expected attrs
    stub = types.ModuleType(submodule_name)
    monkeypatch.setitem(sys.modules, submodule_name, stub)
    sys.modules.pop(module_name, None)

    mod = importlib.import_module(module_name)

    assert mod.get_celery_app is None
    assert mod.is_celery_enabled() is False
    assert mod.submit_task is None
    assert mod.get_task_status is None
    assert mod.cancel_task is None
    assert mod.get_active_tasks() == []
    assert mod.get_celery_stats() == {"enabled": False}


@pytest.mark.unit
def test_services_middleware_import_fallback(monkeypatch):
    module_name = "app.services"
    submodule_name = "app.services.middleware"

    stub = types.ModuleType(submodule_name)
    monkeypatch.setitem(sys.modules, submodule_name, stub)
    sys.modules.pop(module_name, None)

    mod = importlib.import_module(module_name)

    def f(x):
        return x

    assert mod.get_limiter is None
    assert mod.rate_limit_custom("1/minute")(f) is f
    assert mod.setup_rate_limiting(None) is None
    assert mod.get_rate_limit_info(types.SimpleNamespace()) == {"enabled": False}
