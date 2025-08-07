"""System and administrative CRUD operations."""

from .admin import AdminUserCRUD, admin_user_crud
from .audit_log import (
    cleanup_old_audit_logs,
    create_audit_log,
    get_audit_logs_by_event_type,
    get_audit_logs_by_session,
    get_audit_logs_by_user,
    get_failed_audit_logs,
    get_recent_audit_logs,
)

__all__ = [
    # Admin CRUD
    "AdminUserCRUD",
    "admin_user_crud",
    # Audit Log CRUD (actual function names)
    "create_audit_log",
    "get_audit_logs_by_user",
    "get_audit_logs_by_event_type",
    "get_audit_logs_by_session",
    "get_recent_audit_logs",
    "get_failed_audit_logs",
    "cleanup_old_audit_logs",
]
