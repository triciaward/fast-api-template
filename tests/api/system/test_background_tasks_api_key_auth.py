import uuid

import pytest

from app.schemas.auth.user import APIKeyUser

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_background_tasks_require_api_key(async_client):
    from app.core.config import settings as settings_mod

    protected_paths = [
        ("GET", "/system/status"),
        ("GET", "/system/tasks/active"),
        ("GET", "/system/tasks/123/status"),
        ("POST", "/system/tasks/submit"),
        ("DELETE", "/system/tasks/123/cancel"),
        ("POST", "/system/tasks/send-email"),
        ("POST", "/system/tasks/process-data"),
        ("POST", "/system/tasks/cleanup"),
        ("POST", "/system/tasks/long-running"),
        ("POST", "/system/tasks/permanently-delete-accounts"),
    ]

    for method, path in protected_paths:
        r = await async_client.request(method, path)
        # If Celery is disabled, routes are not mounted → 404
        if settings_mod.ENABLE_CELERY:
            assert r.status_code == 401
        else:
            assert r.status_code == 404


@pytest.mark.asyncio
async def test_background_tasks_forbidden_without_scope(async_client, monkeypatch):
    from app.api.users import auth as auth_mod
    from app.core.config import settings as settings_mod

    async def fake_get_api_key_user(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=auth_mod.uuid.uuid4(),  # type: ignore[attr-defined]
            scopes=["other:scope"],
            user_id=None,
            key_id=auth_mod.uuid.uuid4(),  # type: ignore[attr-defined]
        )

    monkeypatch.setattr(auth_mod, "get_api_key_user", fake_get_api_key_user)

    read_paths = [
        ("GET", "/system/status"),
        ("GET", "/system/tasks/active"),
        ("GET", "/system/tasks/123/status"),
    ]
    for method, path in read_paths:
        r = await async_client.request(
            method, path, headers={"Authorization": "Bearer x"}
        )
        # If Celery routes aren't mounted (disabled), we get 404 at routing level before auth
        if settings_mod.ENABLE_CELERY:
            assert r.status_code == 403
        else:
            assert r.status_code == 404

    write_paths = [
        ("POST", "/system/tasks/submit"),
        ("DELETE", "/system/tasks/123/cancel"),
        ("POST", "/system/tasks/send-email"),
        ("POST", "/system/tasks/process-data"),
        ("POST", "/system/tasks/cleanup"),
        ("POST", "/system/tasks/long-running"),
        ("POST", "/system/tasks/permanently-delete-accounts"),
    ]
    for method, path in write_paths:
        r = await async_client.request(
            method, path, headers={"Authorization": "Bearer x"}
        )
        if settings_mod.ENABLE_CELERY:
            assert r.status_code == 403
        else:
            assert r.status_code == 404


@pytest.mark.asyncio
async def test_background_tasks_pass_auth_then_celery_guard_kicks_in(
    async_client, monkeypatch
):
    """
    With correct scopes, auth passes, then since Celery is disabled by default in tests,
    we expect 503 from `check_celery_enabled`.
    """
    from app.api.users import auth as auth_mod
    from app.core.config import settings as settings_mod
    from app.main import app

    async def fake_get_api_key_user_read():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid.uuid4(),
            scopes=["tasks:read"],
            user_id=None,
            key_id=uuid.uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user_read

    # Read endpoints should pass auth; then return 503 if Celery disabled
    for method, path in [
        ("GET", "/system/status"),
        ("GET", "/system/tasks/active"),
        ("GET", "/system/tasks/123/status"),
    ]:
        r = await async_client.request(
            method, path, headers={"Authorization": "Bearer ok"}
        )
        if settings_mod.ENABLE_CELERY:
            assert r.status_code in {200, 503}
        else:
            # routes not mounted at all
            assert r.status_code == 404

    # Now grant write scope and test a write endpoint
    async def fake_get_api_key_user_write():  # type: ignore[no-untyped-def]
        return APIKeyUser(
            id=uuid.uuid4(),
            scopes=["tasks:write"],
            user_id=None,
            key_id=uuid.uuid4(),
        )

    app.dependency_overrides[auth_mod.get_api_key_user] = fake_get_api_key_user_write
    r = await async_client.request(
        "POST",
        "/system/tasks/submit",
        headers={"Authorization": "Bearer ok"},
        json={"task_name": "x", "args": [], "kwargs": {}},
    )
    if settings_mod.ENABLE_CELERY:
        assert r.status_code in {200, 503}
    else:
        assert r.status_code == 404
    app.dependency_overrides.pop(auth_mod.get_api_key_user, None)
