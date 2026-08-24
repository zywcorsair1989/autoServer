"""
食尚订智能问答系统 - FastAPI 应用程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入模型以确保它们被注册到 Base 中
from app.models import user, conversation, knowledge, document  # noqa: F401

from app.api.v1.api import api_router

app = FastAPI(
    title="食尚订智能问答系统",
    description="基于 RAG 的智能问答系统，使用百炼 AI",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中适当配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 API v1 路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根端点"""
    return {"message": "食尚订智能问答系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}