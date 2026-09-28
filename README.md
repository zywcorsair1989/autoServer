# RAG 智能问答系统

基于 RAG (Retrieval-Augmented Generation) 技术的智能问答系统，支持文档知识库管理和流式对话。

## 项目简介

这是一个完整的 RAG 智能问答系统，集成了百炼 AI 服务，提供：
- 用户认证与权限管理
- 知识库文档管理与向量化检索
- 智能对话与历史记录管理
- 流式响应支持
- Docker 容器化部署

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL 15 + pgvector (向量搜索)
- **ORM**: SQLAlchemy 2.0 (异步)
- **认证**: JWT + OAuth2
- **AI 服务**: 百炼 AI SDK
  - LLM: qwen3.7-max-2026-06-08
  - Embedding: text-embedding-v2
  - Rerank: gte-rerank-v2

### 前端
- **框架**: Vue 3 + Vite
- **语言**: JavaScript
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios

### 部署
- Docker + Docker Compose
- Nginx (反向代理)

## 核心功能

### 🔐 用户认证
- JWT Token 认证
- 用户注册、登录
- 角色权限管理
- 密码加密存储

### 💬 智能对话
- 流式响应支持
- 对话历史管理
- 上下文感知
- 多轮对话

### 📚 知识库管理
- 文档上传（PDF/Word/TXT）
- 自动文本分割
- 向量化存储
- 相似度搜索

### 🧠 RAG 技术
- 查询增强
- 多路召回（关键词 + 向量）
- Rerank 重排
- 上下文融合生成

## 项目结构

```
autoServer/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 业务逻辑
│   │   ├── ai/             # AI 服务
│   │   └── utils/          # 工具函数
│   ├── tests/              # 测试用例
│   ├── requirements.txt    # Python 依赖
│   └── .env.example        # 环境变量模板
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── api/           # API 服务
│   │   ├── router/        # 路由配置
│   │   └── store/         # 状态管理
│   ├── nginx.conf         # Nginx 配置（前端镜像构建时使用）
│   └── package.json       # 前端依赖
├── docker-compose.yml      # Docker 编排
└── README.md              # 项目文档
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (启用 pgvector 扩展)
- Docker & Docker Compose (可选)

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/zywcorsair1989/autoServer.git
cd autoServer

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，填入百炼 API Key

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端：http://localhost
# API 文档：http://localhost/api/v1/docs
```

### 方式二：本地开发

详见 [项目启动文档.md](项目启动文档.md)

## API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

### 主要 API 端点

#### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

#### 对话管理
- `GET /api/v1/conversations/` - 获取对话列表
- `POST /api/v1/conversations/` - 创建新对话
- `POST /api/v1/chat/stream` - 流式发送消息

#### 知识库管理
- `POST /api/v1/knowledge` - 创建知识库
- `POST /api/v1/knowledge/query` - 知识库问答
- `GET /api/v1/knowledge` - 获取知识库列表
- `GET /api/v1/knowledge/{id}` - 获取知识库详情
- `DELETE /api/v1/knowledge/{id}` - 删除知识库

## 测试

### 后端测试

```bash
cd backend
pytest
```

当前测试覆盖：
- ✅ 163 个测试用例全部通过
- ✅ 覆盖所有核心模块

## 开发指南

### 后端开发

```bash
# 虚拟环境统一使用项目根目录的 .venv（不要另建 venv）
source .venv/bin/activate          # 首次: python3.11 -m venv .venv
pip install -r backend/requirements.txt
cd backend && python main.py
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 环境变量

### 必需配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| DATABASE_URL | 数据库连接 | postgresql+asyncpg://user:pass@localhost:5432/db |
| SECRET_KEY | JWT 密钥 | 32位以上的随机字符串 |
| BAILIAN_API_KEY | 百炼 API Key | sk-xxxxxxxx |

### 可选配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEBUG | True | 调试模式 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440 | Token 过期时间 |
| MAX_FILE_SIZE | 52428800 | 文件上传限制 (50MB) |

## 性能特性

- 异步处理：全异步架构，支持高并发
- 连接池：数据库连接池配置 (20 base + 10 overflow)
- 向量索引：pgvector IVFFlat 索引优化
- 流式响应：SSE 流式输出，提升用户体验

## 安全特性

- 密码加密：bcrypt 哈希存储
- JWT 认证：24小时 Token 过期
- 权限控制：基于角色的访问控制
- 文件验证：文件类型白名单 + 大小限制

## 项目亮点

1. **完整的 RAG 实现**：从文档上传到答案生成的完整流程
2. **异步架构**：全异步 FastAPI 应用，性能优异
3. **向量检索**：PostgreSQL + pgvector，无需额外向量数据库
4. **流式响应**：支持 SSE 流式输出，体验流畅
5. **测试覆盖**：163 个测试用例，覆盖核心模块
6. **Docker 部署**：一键容器化部署

## 许可证

MIT License

## 作者

zxx

## 贡献

欢迎提交 Issue 和 Pull Request！