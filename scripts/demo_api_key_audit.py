#!/usr/bin/env python3
"""
Demonstration script for API key audit logging.

This script shows how API key usage is automatically logged to the audit system.
"""

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.security import generate_api_key
from app.crud import api_key as crud_api_key
from app.crud.audit_log import get_audit_logs_by_event_type_sync
from app.database.database import SyncSessionLocal
from app.models import User
from app.schemas.user import APIKeyCreate


def create_test_user(db: Session) -> User:
    """Create a test user for demonstration."""
    user = User(
        email="demo@example.com",
        username="demo_user",
        hashed_password="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_api_key_for_user(db: Session, user: User, label: str) -> tuple[str, str]:
    """Create an API key for the given user."""
    raw_key = generate_api_key()
    api_key_data = APIKeyCreate(
        label=label,
        scopes=["read_events", "write_events"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    api_key = crud_api_key.create_api_key_sync(
        db=db,
        api_key_data=api_key_data,
        user_id=str(user.id),
        raw_key=raw_key,
    )

    return str(api_key.id), raw_key


def create_system_api_key(db: Session, label: str) -> tuple[str, str]:
    """Create a system-level API key (no user)."""
    raw_key = generate_api_key()
    api_key_data = APIKeyCreate(
        label=label,
        scopes=["read_events", "write_events", "admin"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    api_key = crud_api_key.create_api_key_sync(
        db=db,
        api_key_data=api_key_data,
        user_id=None,  # System-level key
        raw_key=raw_key,
    )

    return str(api_key.id), raw_key


def make_api_request(api_key: str, endpoint: str = "/api/v1/users/me/api-key") -> dict:
    """Make an API request using the given key."""
    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.get(endpoint, headers={"Authorization": f"Bearer {api_key}"})
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else None,
            "error": response.json() if response.status_code != 200 else None,
        }


def show_audit_logs(db: Session, api_key_id: str, key_label: str):
    """Show audit logs for the given API key."""

    # Get recent audit logs for this API key
    audit_logs = get_audit_logs_by_event_type_sync(db, "api_key_usage", limit=10)

    # Filter for this specific key
    key_logs = [
        log
        for log in audit_logs
        if log.context and log.context.get("api_key_id") == api_key_id
    ]

    if not key_logs:
        return

    for _i, _log in enumerate(key_logs, 1):
        pass


def main():
    """Main demonstration function."""

    # Create database session
    db = SyncSessionLocal()

    try:
        # Create a test user
        user = create_test_user(db)

        # Create API keys
        user_key_id, user_raw_key = create_api_key_for_user(db, user, "Demo User Key")
        system_key_id, system_raw_key = create_system_api_key(db, "Demo System Key")

        # Make API requests with user key
        make_api_request(user_raw_key)

        # Make API requests with system key
        make_api_request(system_raw_key)

        # Show audit logs for user key
        show_audit_logs(db, user_key_id, "Demo User Key")

        # Show audit logs for system key
        show_audit_logs(db, system_key_id, "Demo System Key")

        # Show summary
        all_logs = get_audit_logs_by_event_type_sync(db, "api_key_usage", limit=100)

        # Group by key
        key_usage = {}
        for log in all_logs:
            if log.context and log.context.get("api_key_id"):
                key_id = log.context["api_key_id"]
                key_usage[key_id] = key_usage.get(key_id, 0) + 1

        for _key_id in key_usage:
            pass

    finally:
        db.close()


if __name__ == "__main__":
    main()
