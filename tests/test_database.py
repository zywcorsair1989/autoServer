import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory, engine


@pytest.mark.asyncio
async def test_database_engine_created():
    """Test that database engine is created"""
    assert engine is not None


@pytest.mark.asyncio
async def test_session_factory_created():
    """Test that session factory is created"""
    assert async_session_factory is not None