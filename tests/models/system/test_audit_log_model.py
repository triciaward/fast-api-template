import types

import pytest

pytestmark = pytest.mark.unit


def test_audit_log_helpers():
    from app.models.system.audit_log import AuditLog

    log = types.SimpleNamespace(
        event_type="login_success",
        user_id=None,
        context=None,
    )

    # is_security_event returns a bool; access the value
    assert AuditLog.is_security_event.__get__(log, AuditLog) is True

    # Anonymous property
    assert AuditLog.is_anonymous.__get__(log, AuditLog) is True

    # Context helpers
    AuditLog.add_context.__get__(log, AuditLog)("k", 1)
    assert AuditLog.get_context.__get__(log, AuditLog)("k") == 1
    assert AuditLog.get_context.__get__(log, AuditLog)("missing", 42) == 42
