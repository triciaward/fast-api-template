import pytest


@pytest.mark.unit
def test_configure_cors_with_origins(monkeypatch):
    from app.core.config import config as cfg
    from app.core.config import cors as cors_mod

    class App:
        def __init__(self):
            self.middlewares = []

        def add_middleware(self, mw, **opts):
            self.middlewares.append((mw, opts))

    app = App()
    monkeypatch.setattr(cfg.settings, "BACKEND_CORS_ORIGINS", "https://x.example.com,https://y.example.com", raising=False)

    cors_mod.configure_cors(app)  # type: ignore[arg-type]

    assert app.middlewares
    _, opts = app.middlewares[0]
    assert opts["allow_origins"] == ["https://x.example.com", "https://y.example.com"]


@pytest.mark.unit
def test_configure_cors_without_origins(monkeypatch):
    from app.core.config import config as cfg
    from app.core.config import cors as cors_mod

    class App:
        def __init__(self):
            self.middlewares = []

        def add_middleware(self, mw, **opts):
            self.middlewares.append((mw, opts))

    app = App()
    monkeypatch.setattr(cfg.settings, "BACKEND_CORS_ORIGINS", "", raising=False)

    cors_mod.configure_cors(app)  # type: ignore[arg-type]
    assert app.middlewares == []
