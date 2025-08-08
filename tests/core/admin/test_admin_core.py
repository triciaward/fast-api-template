import types

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.unit


class DummySession:
    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        class _R:
            def scalar_one_or_none(self):
                return types.SimpleNamespace(id="user-1", is_superuser=True)

        return _R()


@pytest.mark.asyncio
async def test_get_current_user_valid(monkeypatch):
    from app.core.admin import admin as mod

    # Return a payload with subject id
    monkeypatch.setattr(mod.jwt, "decode", lambda t, s, algorithms: {"sub": "user-1"})

    # Ensure the inner import resolves to this function
    async def fake_get_user_by_id(db, user_id: str):
        return types.SimpleNamespace(id=user_id, is_superuser=True)

    import app.crud.auth.user as crud_user_module

    monkeypatch.setattr(crud_user_module, "get_user_by_id", fake_get_user_by_id)

    user = await mod.get_current_user(token="token", db=DummySession())
    assert user.id == "user-1"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    from app.core.admin import admin as mod

    class _Err(Exception):
        pass

    # Simulate JWTError by raising from decode
    monkeypatch.setattr(
        mod.jwt, "decode", lambda *a, **k: (_ for _ in ()).throw(mod.JWTError("bad"))
    )

    with pytest.raises(HTTPException) as ei:
        await mod.get_current_user(token="bad", db=DummySession())
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_require_superuser_allows_superuser():
    from app.core.admin import admin as mod

    user = types.SimpleNamespace(id="u1", is_superuser=True)
    result = await mod.require_superuser(current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_require_superuser_blocks_non_superuser():
    from app.core.admin import admin as mod

    user = types.SimpleNamespace(id="u2", is_superuser=False)
    with pytest.raises(HTTPException) as ei:
        await mod.require_superuser(current_user=user)
    assert ei.value.status_code == 403


def test_admin_only_endpoint_decorator_marks_function():
    from app.core.admin import admin as mod

    @mod.admin_only_endpoint
    def sample() -> int:
        return 1

    assert getattr(sample, "__admin_only__", False) is True
