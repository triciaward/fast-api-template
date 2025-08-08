import uuid

import pytest
from sqlalchemy import Column, Integer
from sqlalchemy.sql import Select

pytestmark = pytest.mark.unit


def test_soft_delete_restore_and_queries():
    from app.database.database import Base
    from app.models.core.base import SoftDeleteMixin, TimestampMixin

    class Dummy(Base, SoftDeleteMixin, TimestampMixin):  # type: ignore[misc, valid-type]
        __tablename__ = "dummy_model"
        id = Column(Integer, primary_key=True, default=1)

    d = Dummy()  # created_at/updated_at are set by DB normally; not required here

    # Initially active
    assert d.is_active is True

    # Soft delete
    deleter = uuid.uuid4()
    d.soft_delete(deleted_by=deleter, reason="cleanup")
    assert d.is_deleted is True
    assert d.deleted_at is not None
    assert d.deleted_by == deleter
    assert d.deletion_reason == "cleanup"

    # Restore
    d.restore()
    assert d.is_deleted is False
    assert d.deleted_at is None
    assert d.deleted_by is None
    assert d.deletion_reason is None
    assert d.is_active is True

    # Query builders return Select objects
    assert isinstance(Dummy.get_active_query(), Select)
    assert isinstance(Dummy.get_deleted_query(), Select)
    assert isinstance(Dummy.get_all_query(), Select)


