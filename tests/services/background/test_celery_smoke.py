import pytest


def test_is_celery_enabled_flag(monkeypatch):
    from app.services.background import celery as celery_service

    # Ensure disabled by default in template
    monkeypatch.setattr(celery_service, "is_celery_enabled", lambda: False)
    assert celery_service.is_celery_enabled() is False
    assert celery_service.get_task_status("x") is None
    assert celery_service.cancel_task("x") is False
    assert celery_service.get_active_tasks() == []
    assert celery_service.get_celery_stats()["enabled"] is False


@pytest.mark.skipif(True, reason="Celery broker not configured in template by default")
def test_submit_task_eager_mode(monkeypatch):
    from app.services.background import celery as celery_service
    from app.services.background.celery_app import celery_app

    # Simulate enabled and eager execution
    monkeypatch.setattr(celery_service, "is_celery_enabled", lambda: True)
    celery_app.conf.task_always_eager = True
    res = celery_service.submit_task("app.services.celery_tasks.cleanup_task")
    assert res is not None

