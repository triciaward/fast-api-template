import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_async_basic() -> None:
    """Basic async test to verify pytest-asyncio is working."""
    await asyncio.sleep(0.1)
    assert True


@pytest.mark.asyncio
async def test_async_session_type(db_session: AsyncSession) -> None:
    """Test that db_session fixture returns correct type."""
    assert isinstance(db_session, AsyncSession)
    assert hasattr(db_session, "add")
    assert hasattr(db_session, "commit")
    assert hasattr(db_session, "refresh")
