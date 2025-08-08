import types
import uuid

import pytest

pytestmark = pytest.mark.unit


def _admin():
    return types.SimpleNamespace(id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"))


@pytest.mark.asyncio
async def test_bulk_operations_mixed_and_invalid(monkeypatch, async_client):
    from app.api.admin import users as mod
    from app.main import app

    app.dependency_overrides[mod.require_superuser] = lambda: _admin()

    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    calls = {"n": 0}

    async def toggle_ver(db, uid):
        # return user objects alternating between verified/unverified and None (failure)
        calls["n"] += 1
        if calls["n"] == 1:
            return types.SimpleNamespace(is_verified=False)
        if calls["n"] == 2:
            return None
        return types.SimpleNamespace(is_verified=True)

    monkeypatch.setattr(mod.admin_user_crud, "toggle_verification_status", toggle_ver)

    # verify: first id toggles twice to become verified, second fails, third already verified counts success
    r = await async_client.post("/admin/bulk-operations", json={"operation": "verify", "user_ids": [str(i) for i in ids]})
    assert r.status_code == 200
    body = r.json()
    assert body["successful"] == 2 and body["failed"] == 1 and len(body["failed_user_ids"]) == 1

    # invalid operation should mark all as failed
    r = await async_client.post("/admin/bulk-operations", json={"operation": "noop", "user_ids": [str(i) for i in ids]})
    app.dependency_overrides.clear()
    assert r.status_code == 422 or r.json()["failed"] == 3
