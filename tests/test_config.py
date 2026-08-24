import pytest
from app.core.config import settings


def test_config_has_required_fields():
    """Test that config has all required fields"""
    assert settings.PROJECT_NAME is not None
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
    assert settings.BAILIAN_API_KEY is not None
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440