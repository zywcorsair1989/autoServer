"""Pytest configuration and fixtures."""

import pytest
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from app.core.config import Settings
    return Settings(
        SECRET_KEY="test-secret-key-for-testing-min-32-chars",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30
    )