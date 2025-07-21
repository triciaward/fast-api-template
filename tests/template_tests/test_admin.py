"""Tests for admin-only functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.crud.admin import admin_user_crud
from app.crud.user import create_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_admin_user_crud_operations(db_session: AsyncSession) -> None:
    """Test admin CRUD operations."""
    # Create a regular user
    user_data = UserCreate(
        email="admin@test.com",
        username="adminuser",
        password="TestPassword123!",
        is_superuser=False,
    )
    await create_user(db_session, user_data)

    # Create a superuser
    superuser_data = UserCreate(
        email="super@test.com",
        username="superuser",
        password="TestPassword123!",
        is_superuser=True,
    )
    await create_user(db_session, superuser_data)

    # Test get_users with filters
    users = await admin_user_crud.get_users(db_session, is_superuser=True)
    assert len(users) == 1
    assert users[0].email == "super@test.com"

    users = await admin_user_crud.get_users(db_session, is_superuser=False)
    assert len(users) == 1
    assert users[0].email == "admin@test.com"

    # Test get_user_by_email
    user = await admin_user_crud.get_user_by_email(db_session, "admin@test.com")
    assert user is not None
    assert user.email == "admin@test.com"

    # Test get_user_by_username
    user = await admin_user_crud.get_user_by_username(db_session, "adminuser")
    assert user is not None
    assert user.username == "adminuser"

    # Test count
    total_count = await admin_user_crud.count(db_session)
    assert total_count == 2

    superuser_count = await admin_user_crud.count(db_session, {"is_superuser": True})
    assert superuser_count == 1


@pytest.mark.asyncio
async def test_admin_user_toggle_operations(db_session: AsyncSession) -> None:
    """Test admin user toggle operations."""
    # Create a test user
    user_data = UserCreate(
        email="toggle@test.com",
        username="toggleuser",
        password="TestPassword123!",
        is_superuser=False,
    )
    user = await create_user(db_session, user_data)

    # Test toggle superuser status
    updated_user = await admin_user_crud.toggle_superuser_status(
        db_session, str(user.id)
    )
    assert updated_user is not None
    assert updated_user.is_superuser is True

    # Toggle back
    updated_user = await admin_user_crud.toggle_superuser_status(
        db_session, str(user.id)
    )
    assert updated_user is not None
    assert updated_user.is_superuser is False

    # Test toggle verification status
    updated_user = await admin_user_crud.toggle_verification_status(
        db_session, str(user.id)
    )
    assert updated_user is not None
    assert updated_user.is_verified is True

    # Toggle back
    updated_user = await admin_user_crud.toggle_verification_status(
        db_session, str(user.id)
    )
    assert updated_user is not None
    assert updated_user.is_verified is False


@pytest.mark.asyncio
async def test_admin_user_statistics(db_session: AsyncSession) -> None:
    """Test admin user statistics."""
    # Create test users
    regular_user_data = UserCreate(
        email="stats1@test.com",
        username="statsuser1",
        password="TestPassword123!",
        is_superuser=False,
    )
    await create_user(db_session, regular_user_data)

    superuser_data = UserCreate(
        email="stats2@test.com",
        username="statsuser2",
        password="TestPassword123!",
        is_superuser=True,
    )
    await create_user(db_session, superuser_data)

    # Get statistics
    stats = await admin_user_crud.get_user_statistics(db_session)

    assert stats["total_users"] == 2
    assert stats["superusers"] == 1
    assert stats["regular_users"] == 1
    assert stats["verified_users"] == 0
    assert stats["unverified_users"] == 2


def test_admin_endpoints_require_superuser(
    client: TestClient, sync_db_session: Session
) -> None:
    """Test that admin endpoints require superuser privileges."""
    # Test without authentication
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401

    # Test with regular user authentication
    # First create a regular user directly in database
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="regular@test.com",
        username="regularuser",
        password="TestPassword123!",
        is_superuser=False,
    )
    user = crud_user.create_user_sync(sync_db_session, user_data)
    user.is_verified = True  # type: ignore[assignment]
    sync_db_session.commit()

    # Login as regular user
    login_data = {
        "username": "regular@test.com",
        "password": "TestPassword123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Try to access admin endpoint with regular user token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


def test_admin_endpoints_with_superuser(
    client: TestClient, sync_db_session: Session
) -> None:
    """Test admin endpoints with superuser authentication."""
    # Create a superuser directly in database
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="admin@test.com",
        username="adminuser",
        password="TestPassword123!",
        is_superuser=True,
    )
    user = crud_user.create_user_sync(sync_db_session, user_data)
    user.is_verified = True  # type: ignore[assignment]
    sync_db_session.commit()

    # Login as superuser
    login_data = {
        "username": "admin@test.com",
        "password": "TestPassword123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Test admin endpoints
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200

    response = client.get("/api/v1/admin/statistics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "superusers" in data


def test_admin_user_management(client: TestClient, sync_db_session: Session) -> None:
    """Test admin user management operations."""
    # Create a superuser directly in database
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="admin@test.com",
        username="adminuser",
        password="TestPassword123!",
        is_superuser=True,
    )
    user = crud_user.create_user_sync(sync_db_session, user_data)
    user.is_verified = True  # type: ignore[assignment]
    sync_db_session.commit()

    # Login as superuser
    login_data = {
        "username": "admin@test.com",
        "password": "TestPassword123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Create a new user via admin
    new_user_data = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "TestPassword123!",
        "is_superuser": False,
        "is_verified": True,
    }
    response = client.post("/api/v1/admin/users", json=new_user_data, headers=headers)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Get user details
    response = client.get(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@test.com"

    # Update user
    update_data = {
        "username": "updateduser",
        "is_verified": False,
    }
    response = client.put(
        f"/api/v1/admin/users/{user_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["username"] == "updateduser"
    assert response.json()["is_verified"] is False

    # Toggle superuser status
    response = client.post(
        f"/api/v1/admin/users/{user_id}/toggle-superuser", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_value"] is True

    # Toggle verification status
    response = client.post(
        f"/api/v1/admin/users/{user_id}/toggle-verification", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["new_value"] is True

    # Delete user
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code == 204


def test_admin_bulk_operations(client: TestClient, sync_db_session: Session) -> None:
    """Test admin bulk operations."""
    # Create a superuser directly in database
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="admin@test.com",
        username="adminuser",
        password="TestPassword123!",
        is_superuser=True,
    )
    user = crud_user.create_user_sync(sync_db_session, user_data)
    user.is_verified = True  # type: ignore[assignment]
    sync_db_session.commit()

    # Login as superuser
    login_data = {
        "username": "admin@test.com",
        "password": "TestPassword123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple users
    user_ids = []
    for i in range(3):
        new_user_data = {
            "email": f"bulkuser{i}@test.com",
            "username": f"bulkuser{i}",
            "password": "TestPassword123!",
            "is_superuser": False,
            "is_verified": False,
        }
        response = client.post(
            "/api/v1/admin/users", json=new_user_data, headers=headers
        )
        assert response.status_code == 201
        user_ids.append(response.json()["id"])

    # Test bulk verify
    bulk_data = {
        "user_ids": user_ids,
        "operation": "verify",
    }
    response = client.post(
        "/api/v1/admin/bulk-operations", json=bulk_data, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "verify"
    assert data["total_users"] == 3
    assert data["successful"] == 3
    assert data["failed"] == 0

    # Test bulk unverify
    bulk_data = {
        "user_ids": user_ids,
        "operation": "unverify",
    }
    response = client.post(
        "/api/v1/admin/bulk-operations", json=bulk_data, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "unverify"
    assert data["total_users"] == 3
    assert data["successful"] == 3
    assert data["failed"] == 0


def test_admin_self_protection(client: TestClient, sync_db_session: Session) -> None:
    """Test that admins cannot delete or modify their own accounts."""
    # Create a superuser directly in database
    from app.crud import user as crud_user
    from app.schemas.user import UserCreate

    user_data = UserCreate(
        email="admin@test.com",
        username="adminuser",
        password="TestPassword123!",
        is_superuser=True,
    )
    user = crud_user.create_user_sync(sync_db_session, user_data)
    user.is_verified = True  # type: ignore[assignment]
    sync_db_session.commit()

    # Login as superuser
    login_data = {
        "username": "admin@test.com",
        "password": "TestPassword123!",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    user_id = str(user.id)

    headers = {"Authorization": f"Bearer {token}"}

    # Try to delete own account
    response = client.delete(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code == 400
    assert "Cannot delete your own account" in response.json()["error"]["message"]

    # Try to toggle own superuser status
    response = client.post(
        f"/api/v1/admin/users/{user_id}/toggle-superuser", headers=headers
    )
    assert response.status_code == 400
    assert (
        "Cannot modify your own superuser status" in response.json()["error"]["message"]
    )
