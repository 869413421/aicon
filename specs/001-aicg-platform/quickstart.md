# 快速开始指南: AICG内容分发平台

**创建日期**: 2025-11-06
**版本**: 1.0.0
**目标用户**: 开发者和系统管理员

## 系统概览

AICG内容分发平台是一个AI驱动的长文本到视频自动转换系统，支持：

- **超长文本处理**: 支持百万字级文档的章节自动识别和分割
- **智能视频生成**: 基于句子级别的图片、音频、字幕自动生成
- **多平台分发**: 支持B站、YouTube等平台的内容发布
- **异步任务队列**: 高并发处理能力，支持100+并发任务
- **实时进度跟踪**: WebSocket实时进度推送
- **API密钥管理**: 支持多供应商AI服务配置

## 技术栈

### 后端技术栈
- **语言**: Python 3.11+
- **Web框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+ (主数据库), Redis 7.0 (缓存/队列)
- **ORM**: SQLAlchemy 2.0 (异步)
- **任务队列**: Celery 5.3+ + Redis
- **对象存储**: MinIO (S3兼容)
- **视频处理**: FFmpeg + ffmpeg-python
- **包管理**: uv (10-100倍速度提升)

### 前端技术栈
- **框架**: Vue.js 3+
- **构建工具**: Vite
- **状态管理**: Pinia
- **UI组件**: Element Plus (推荐)
- **HTTP客户端**: Axios
- **实时通信**: WebSocket

### 基础设施
- **容器化**: Docker + Docker Compose
- **监控**: Prometheus + Grafana
- **日志**: structlog + OpenTelemetry
- **代理**: Nginx (生产环境)

## 环境要求

### 开发环境
```bash
# 系统要求
操作系统: Linux/macOS/Windows (WSL2)
Python: 3.11+
Node.js: 18+
Docker: 20.10+
Docker Compose: 2.0+

# 硬件要求
内存: 8GB+ (推荐16GB)
存储: 50GB+ 可用空间
CPU: 4核心+ (推荐8核心)
```

### 生产环境
```bash
# 最低配置
CPU: 8核心
内存: 32GB
存储: 500GB SSD
网络: 100Mbps+

# 推荐配置
CPU: 16核心
内存: 64GB
存储: 1TB NVMe SSD
网络: 1Gbps
```

## 快速部署 (Docker Compose)

### 1. 克隆项目

```bash
git clone https://github.com/your-org/aicg-platform.git
cd aicg-platform
```

### 2. 环境配置

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

**.env 配置示例**:
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://aicg_user:aicg_password@postgres:5432/aicg_db
REDIS_URL=redis://redis:6379/0

# MinIO配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# MinIO端口说明
# API端口: 9000 (服务间调用)
# Web控制台: 9001 (浏览器访问)

# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API配置
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# 日志配置
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
docker compose exec backend uv run alembic upgrade head

# 创建初始用户 (可选)
docker compose exec backend uv run python scripts/create_admin.py
```

### 5. 访问应用

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **MinIO控制台**: http://localhost:9001 (admin/admin123)
- **MinIO服务端口**: 9000 (API), 9001 (Web控制台)
- **Redis Inspector**: http://localhost:8001/redis
- **Grafana监控**: http://localhost:3002 (admin/admin123)

## 开发环境搭建

### 1. 安装依赖

#### 后端依赖 (uv)

```bash
cd backend

# 安装uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 直接同步依赖，uv会自动创建虚拟环境并安装所有依赖
uv sync

# 运行命令 (无需手动激活虚拟环境)
uv run python --version
uv run uvicorn src.main:app --reload
```

#### 前端依赖

```bash
cd frontend

# 安装依赖
npm install
# 或
yarn install
```

### 2. 本地开发

#### 启动后端服务

```bash
cd backend

# 启动数据库和Redis (如果使用Docker)
docker compose up -d postgres redis minio

# 运行数据库迁移
uv run alembic upgrade head

# 启动API服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker (新终端)
uv run celery -A src.workers.base worker --loglevel=info --concurrency=4

# 启动Celery Beat (新终端) - 定时任务
uv run celery -A src.workers.base beat --loglevel=info
```

#### 启动前端服务

```bash
cd frontend

# 开发模式启动
npm run dev
# 或
yarn dev
```

### 3. 开发工具配置

#### VS Code配置

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

**.vscode/extensions.json**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.pylint",
    "Vue.volar",
    "Vue.vscode-vue-plugin",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json"
  ]
}
```

#### Git Hooks (pre-commit)

```bash
# 安装pre-commit
uv add --dev pre-commit

# 安装hooks
uv run pre-commit install

# 手动运行
uv run pre-commit run --all-files
```

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## 核心功能使用

### 1. 用户注册和登录

```bash
# 注册用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
  }'

# 登录获取Token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 2. 上传文档

```bash
# 上传文档
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/novel.txt"
```

### 3. 项目管理

```bash
# 创建项目
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的小说",
    "description": "这是一个测试小说项目",
    "file_id": "uploaded_file_id"
  }'

# 获取项目列表
curl -X GET "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. 章节处理

```bash
# 获取章节列表
curl -X GET "http://localhost:8000/api/v1/projects/{project_id}/chapters" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 确认章节
curl -X PUT "http://localhost:8000/api/v1/chapters/{chapter_id}/confirm" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmed_paragraphs": [
      {"id": "para1", "action": "keep"},
      {"id": "para2", "content": "修改后的内容", "action": "edit"}
    ]
  }'
```

### 5. API配置

```bash
# 添加AI服务配置
curl -X POST "http://localhost:8000/api/v1/api-configs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "火山引擎图片生成",
    "provider": "volcengine",
    "service_type": "image_generation",
    "api_key": "your_api_key_here",
    "endpoint": "https://api.volcengine.com",
    "is_active": true
  }'
```

### 6. 视频生成

```bash
# 启动批量生成
curl -X POST "http://localhost:8000/api/v1/generation/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chapter_ids": ["chapter1_id", "chapter2_id"],
    "api_config_id": "api_config_id",
    "generation_settings": {
      "video_style": "cinematic",
      "voice_type": "female_gentle",
      "background_music": true
    }
  }'

# 查看生成进度
curl -X GET "http://localhost:8000/api/v1/generation/tasks/{task_id}/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 监控和运维

### 1. 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db

# Redis连接检查
curl http://localhost:8000/health/redis

# Celery状态检查
curl http://localhost:8000/health/celery
```

### 2. 日志查看

```bash
# 应用日志
docker compose logs -f backend

# Celery日志
docker compose logs -f celery-worker

# 数据库日志
docker compose logs -f postgres

# 所有服务日志
docker compose logs -f
```

### 3. 性能监控

访问Grafana监控面板:
- URL: http://localhost:3002
- 用户名: admin
- 密码: admin123

监控指标包括:
- API响应时间
- 任务队列长度
- 数据库连接数
- 内存和CPU使用率
- 存储使用情况

### 4. 数据备份

```bash
# 数据库备份
docker compose exec postgres pg_dump -U aicg_user aicg_db > backup.sql

# MinIO数据备份
docker compose exec minio mc mirror /data ./minio-backup

# 自动备份脚本
./scripts/backup.sh
```

## 常见问题解决

### 1. 端口冲突

```bash
# 修改docker-compose.yml中的端口映射
services:
  backend:
    ports:
      - "8001:8000"  # 改为8001
```

### 2. 内存不足

```bash
# 增加Docker内存限制
docker compose up -d --scale worker=2

# 或者修改docker-compose.yml
services:
  celery-worker:
    deploy:
      resources:
        limits:
          memory: 2G
```

### 3. 文件上传失败

```bash
# 检查MinIO状态
docker compose exec minio mc admin info local

# 检查存储空间
docker compose exec minio mc df local
```

### 4. 任务队列堵塞

```bash
# 查看Celery队列状态
docker compose exec backend uv run celery -A src.workers.base inspect active

# 清空队列
docker compose exec backend uv run celery -A src.workers.base purge
```

## 测试策略

### 测试数据管理

#### E2E测试数据准备
```bash
# 创建测试数据目录
mkdir -p tests/e2e/fixtures/{test-documents,test-images,test-videos}

# 测试文档示例
tests/e2e/fixtures/test-documents/
├── short-story.txt           # 短篇故事 (1千字)
├── novel-sample.txt           # 小说样本 (1万字)
├── multi-chapter.md          # 多章节文档
└── complex-format.docx       # 复杂格式文档

# 测试API密钥 (开发环境)
tests/e2e/fixtures/test-api-keys.json
{
  "test_image_key": "test_image_key_value",
  "test_audio_key": "test_audio_key_value"
}
```

#### 测试环境配置
```javascript
// tests/e2e/utils/test-setup.js
export const testConfig = {
  baseURL: 'http://localhost:8000',
  frontendURL: 'http://localhost:3000',
  defaultTimeout: 30000,
  retries: 2
};

export const testUsers = {
  valid: {
    username: 'testuser',
    email: 'test@example.com',
    password: 'testpassword123'
  }
};
```

### 数据库迁移最佳实践

#### 开发环境迁移
```bash
# 检查迁移状态
uv run alembic current

# 创建新迁移
uv run alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
uv run alembic upgrade head

# 回滚迁移（如需要）
uv run alembic downgrade -1
```

#### 生产环境迁移
```bash
# 备份数据库
docker compose exec postgres pg_dump -U aicg_user aicg_db > backup-$(date +%Y%m%d).sql

# 测试迁移文件
uv run alembic upgrade head --sql

# 执行迁移
uv run alembic upgrade head

# 验证迁移结果
docker compose exec backend uv run python scripts/verify-migration.py
```

## 开发指南

### 1. 添加新依赖

```bash
# 添加新的生产依赖
uv add fastapi sqlalchemy

# 添加开发依赖
uv add --dev pytest black
```

### 2. 添加新API端点

```python
# src/api/v1/new_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db

router = APIRouter()

@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    # 实现逻辑
    pass

# 注册路由
# src/api/v1/__init__.py
from .new_feature import router as new_feature_router
api_router.include_router(new_feature_router, prefix="/new-feature", tags=["new-feature"])
```

### 3. 添加新模型

```python
# models/new_model.py
from sqlalchemy import Column, String, Text
from models.base import Base

class NewModel(Base):
    __tablename__ = 'new_models'

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

# 运行迁移
uv run alembic revision --autogenerate -m "Add NewModel"
uv run alembic upgrade head
```

### 4. 添加新任务

```python
# workers/new_tasks.py
from celery import Celery
from workers.base import app

@app.task
def process_new_task(data: dict):
    # 实现任务逻辑
    return {"status": "completed", "result": data}
```

## 生产部署

### 1. 环境准备

```bash
# 生产环境配置
cp docker-compose.prod.yml docker-compose.override.yml

# 设置生产环境变量
export NODE_ENV=production
export LOG_LEVEL=WARNING
```

### 2. SSL配置

```bash
# 使用Let's Encrypt获取SSL证书
certbot certonly --webroot -w /var/www/html -d yourdomain.com

# 配置Nginx SSL
# nginx/nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
}
```

### 3. 性能优化

```bash
# 数据库连接池优化
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

# Redis连接优化
REDIS_CONNECTION_POOL = {
    "max_connections": 100,
    "retry_on_timeout": True
}
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

- **文档**: [项目文档](https://docs.aicg-platform.com)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/aicg-platform/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-org/aicg-platform/discussions)
- **邮件**: support@aicg-platform.com

---

**快速开始版本**: 1.0.0
**最后更新**: 2025-11-06
**维护者**: AICG Platform Team