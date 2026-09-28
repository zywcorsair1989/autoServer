from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# .env 位于 backend 目录；使用绝对路径，避免从不同工作目录启动时读不到配置
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """应用设置，从环境变量加载"""

    # 项目
    PROJECT_NAME: str = "食尚订智能问答系统"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: str = "*"  # 生产环境应设置为具体域名，多个用逗号分隔

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_system"

    # 安全
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 小时

    # 百炼 AI
    BAILIAN_API_KEY: str = ""
    BAILIAN_LLM_MODEL: str = "qwen3.7-max-2026-06-08"
    BAILIAN_EMBEDDING_MODEL: str = "text-embedding-v2"
    BAILIAN_RERANK_MODEL: str = "gte-rerank-v2"

    # 文件上传
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.txt"

    # 向量
    # 必须与 BAILIAN_EMBEDDING_MODEL 实际输出维度一致（qwen3.7-text-embedding 为 1024），
    # 不一致会导致 pgvector 写入/检索时报维度错误，详见 migrations/003
    EMBEDDING_DIMENSION: int = 1024
    CONTEXT_LIMIT: int = 5

    @property
    def allowed_extensions_list(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(',')]

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        case_sensitive=True
    )


settings = Settings()