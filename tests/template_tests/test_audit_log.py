import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.audit_log import create_audit_log_sync, get_audit_logs_by_user_sync
from app.services.audit import log_event_sync, log_login_attempt_sync


def test_create_audit_log_sync(sync_db_session: Session):
    """Test creating an audit log entry."""
    test_user_id = str(uuid.uuid4())
    audit_log = create_audit_log_sync(
        db=sync_db_session,
        event_type="test_event",
        user_id=test_user_id,
        ip_address="127.0.0.1",
        user_agent="test-agent",
        success=True,
        context={"test": "data"},
        session_id="test-session",
    )

    assert audit_log.id is not None
    assert audit_log.event_type == "test_event"
    assert str(audit_log.user_id) == test_user_id
    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.user_agent == "test-agent"
    assert audit_log.success is True
    assert audit_log.context == {"test": "data"}
    assert audit_log.session_id == "test-session"
    assert audit_log.timestamp is not None


def test_get_audit_logs_by_user_sync(sync_db_session: Session):
    """Test retrieving audit logs for a user."""
    # Create test audit logs
    user_id = str(uuid.uuid4())
    create_audit_log_sync(sync_db_session, "event1", user_id=user_id)
    create_audit_log_sync(sync_db_session, "event2", user_id=user_id)
    create_audit_log_sync(sync_db_session, "event3", user_id=str(uuid.uuid4()))

    # Get logs for the test user
    logs = get_audit_logs_by_user_sync(sync_db_session, user_id)

    assert len(logs) == 2
    assert all(str(log.user_id) == user_id for log in logs)
    # Should be ordered by timestamp desc
    assert logs[0].timestamp >= logs[1].timestamp


def test_log_event_sync(sync_db_session: Session, client: TestClient):
    """Test the log_event function."""
    from fastapi import Request

    # Create a mock request
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [
                (b"user-agent", b"test-agent"),
                (b"x-forwarded-for", b"192.168.1.1"),
            ],
            "client": ("127.0.0.1", 12345),
        },
    )

    # Test logging an event
    log_event_sync(
        db=sync_db_session,
        event_type="test_event",
        request=request,
        user=None,
        success=True,
        context={"test": "data"},
        session_id="test-session",
    )

    # Verify the log was created
    logs = get_audit_logs_by_user_sync(sync_db_session, "")  # Get anonymous logs
    assert len(logs) == 1
    assert logs[0].event_type == "test_event"
    assert logs[0].ip_address == "192.168.1.1"  # Should use X-Forwarded-For
    assert logs[0].user_agent == "test-agent"
    assert logs[0].success is True
    assert logs[0].context == {"test": "data"}
    assert logs[0].session_id == "test-session"


def test_log_login_attempt_sync(sync_db_session: Session, client: TestClient):
    """Test logging login attempts."""
    from fastapi import Request

    # Create a mock request
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/login",
            "headers": [(b"user-agent", b"test-agent")],
            "client": ("127.0.0.1", 12345),
        },
    )

    # Test successful login
    log_login_attempt_sync(
        db=sync_db_session,
        request=request,
        user=None,
        success=True,
        oauth_provider="google",
    )

    # Test failed login
    log_login_attempt_sync(
        db=sync_db_session,
        request=request,
        user=None,
        success=False,
    )

    # Verify the logs were created - filter by event type to avoid other test logs
    all_logs = get_audit_logs_by_user_sync(sync_db_session, "")  # Get anonymous logs
    login_logs = [
        log for log in all_logs if log.event_type in ["login_success", "login_failed"]
    ]
    assert len(login_logs) == 2

    # Check successful login
    success_log = next(log for log in login_logs if log.event_type == "login_success")
    assert success_log.success is True
    assert success_log.context == {"oauth_provider": "google"}

    # Check failed login
    failed_log = next(log for log in login_logs if log.event_type == "login_failed")
    assert failed_log.success is False
    assert failed_log.context == {}


def test_audit_log_model_repr(sync_db_session: Session):
    """Test the AuditLog model __repr__ method."""
    test_user_id = str(uuid.uuid4())
    audit_log = create_audit_log_sync(
        db=sync_db_session,
        event_type="test_event",
        user_id=test_user_id,
        success=True,
    )

    repr_str = repr(audit_log)
    assert "AuditLog" in repr_str
    assert "test_event" in repr_str
    assert str(test_user_id) in repr_str
    assert "True" in repr_str  # success=True
