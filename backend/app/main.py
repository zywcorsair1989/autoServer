"""
食尚订智能问答系统 - FastAPI 应用程序
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 导入模型以确保它们被注册到 Base 中
from app.models import user, conversation, knowledge, document  # noqa: F401

from app.api.v1.api import api_router
from app.core.config import settings

# 安全检查：生产环境必须设置 SECRET_KEY
DEFAULT_SECRET_KEY = "your-secret-key-change-in-production-min-32-characters"
if settings.SECRET_KEY == DEFAULT_SECRET_KEY:
    import sys
    print("错误：SECRET_KEY 使用默认值，请设置环境变量 SECRET_KEY")
    sys.exit(1)

app = FastAPI(
    title="食尚订智能问答系统",
    description="基于 RAG 的智能问答系统，使用百炼 AI",
    version="1.0.0",
)

# 配置 CORS
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
# 当 allow_credentials=True 时，不能使用通配符 "*"
allow_credentials = settings.CORS_ORIGINS != "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 API v1 路由
app.include_router(api_router, prefix="/api/v1")

# 静态挂载上传目录：检索命中后前端通过 /uploads/images/{doc_id}/xxx 直接访问文档图片
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    """根端点"""
    return {"message": "食尚订智能问答系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}