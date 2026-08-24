from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Project
    PROJECT_NAME: str = "RAG Intelligent Q&A System"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_system"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Bailian AI
    BAILIAN_API_KEY: str = ""
    BAILIAN_LLM_MODEL: str = "qwen3.7-max-2026-06-08"
    BAILIAN_EMBEDDING_MODEL: str = "text-embedding-v2"
    BAILIAN_RERANK_MODEL: str = "gte-rerank-v2"

    # File Upload
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.txt"

    # Vector
    EMBEDDING_DIMENSION: int = 1536
    CONTEXT_LIMIT: int = 5

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get list of allowed file extensions"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(',')]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()