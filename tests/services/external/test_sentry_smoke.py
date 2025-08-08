import pytest


def test_sentry_disabled_path(monkeypatch):
    from app.services.external import sentry as sentry_service

    # Force disabled
    monkeypatch.setattr(sentry_service, "is_sentry_working", lambda: False)
    assert sentry_service.is_sentry_working() is False
    # Ensure helpers no-op when disabled
    sentry_service.capture_message("x")
    sentry_service.capture_exception(Exception("x"))
    sentry_service.set_user_context(user_id=1, email="a@b.com")
    sentry_service.clear_user_context()
    # No exceptions should be raised


@pytest.mark.skip(
    reason="Sentry DSN not configured in template; enable to test init path",
)
def test_sentry_init_when_enabled(monkeypatch):
    from app.services.external import sentry as sentry_service

    calls = {"init": 0}

    class FakeClient:
        transport = object()

    def fake_init(**kwargs):
        calls["init"] += 1

    monkeypatch.setattr(
        sentry_service,
        "settings",
        type(
            "S",
            (),
            {
                "ENABLE_SENTRY": True,
                "SENTRY_DSN": "http://example.com/1",
                "SENTRY_ENVIRONMENT": "test",
                "SENTRY_TRACES_SAMPLE_RATE": 0.0,
                "SENTRY_PROFILES_SAMPLE_RATE": 0.0,
                "ENABLE_REDIS": False,
                "ENABLE_CELERY": False,
                "ENVIRONMENT": "test",
                "VERSION": "0.0.0",
            },
        ),
    )
    monkeypatch.setattr(
        sentry_service,
        "sentry_sdk",
        type(
            "SDK",
            (),
            {
                "init": staticmethod(fake_init),
                "set_tag": staticmethod(lambda *args, **kwargs: None),
                "Hub": type(
                    "H", (), {"current": type("C", (), {"client": FakeClient()})},
                ),
            },
        ),
    )

    sentry_service.init_sentry()
    assert calls["init"] == 1
