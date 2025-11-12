"""
简化的pytest配置文件，避免循环依赖
"""

import pytest
import asyncio
import tempfile
import os
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_text_content():
    """示例文本内容"""
    return """# 测试文档

这是一个测试文档内容。

## 第一章

第一章内容...

### 1.1 小节

小节内容...

## 第二章

第二章内容...

包含一些测试数据：
- 项目1
- 项目2
- 项目3

这是文档的结尾。
"""


@pytest.fixture
def sample_markdown_content():
    """示例Markdown内容"""
    return """# 测试Markdown文档

这是一个**测试**Markdown文档。

## 功能特性

- 支持**粗体**
- 支持*斜体*
- 支持`代码`
- 支持[链接](https://example.com)

## 代码示例

```python
def hello_world():
    print("Hello, World!")
    return True
```

## 列表

1. 第一项
2. 第二项
3. 第三项

> 这是一个引用块

## 表格

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| 1   | 2   | 3   |
"""


@pytest.fixture
def test_file_factory():
    """测试文件工厂函数"""
    def create_test_file(content=None, suffix=".txt", encoding="utf-8"):
        if content is None:
            content = "This is a test file content."

        if isinstance(content, str):
            content = content.encode(encoding)

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name

        return temp_path

    return create_test_file


@pytest.fixture
def mock_storage_client():
    """模拟存储客户端"""
    storage = Mock()
    storage.bucket_name = "test-bucket"

    # 配置默认返回值
    storage.upload_file = AsyncMock(return_value={
        "success": True,
        "bucket": "test-bucket",
        "object_key": "uploads/test/test.txt",
        "size": 1024,
        "etag": "test-etag",
        "url": "http://test-url"
    })

    storage.download_file = AsyncMock(return_value=b"test content")
    storage.delete_file = AsyncMock(return_value=True)
    storage.get_presigned_url = AsyncMock(return_value="http://presigned-url.com/file")
    storage.get_file_info = AsyncMock(return_value={
        "object_key": "uploads/test/test.txt",
        "size": 1024,
        "url": "http://test-url"
    })
    storage.copy_file = AsyncMock(return_value=True)
    storage.file_exists = AsyncMock(return_value=True)
    storage.list_files = AsyncMock(return_value=[])

    return storage


@pytest.fixture
def mock_project_service():
    """模拟项目服务"""
    service = Mock()

    # 配置默认返回值
    service.create_project = AsyncMock(return_value=Mock(
        id="project-123",
        title="Test Project",
        status="active"
    ))

    service.get_project_by_id = AsyncMock(return_value=Mock(
        id="project-123",
        title="Test Project"
    ))

    service.get_user_projects = AsyncMock(return_value=([], 0))
    service.update_project = AsyncMock(return_value=Mock(
        id="project-123",
        title="Updated Project"
    ))

    service.delete_project = AsyncMock(return_value=True)
    service.restore_project = AsyncMock(return_value=True)
    service.update_processing_status = AsyncMock(return_value=True)
    service.start_file_processing = AsyncMock(return_value=True)
    service.get_processing_task_status = AsyncMock(return_value={
        "task_id": "task-123",
        "status": "completed",
        "result": None,
        "traceback": None
    })

    service.get_project_statistics = AsyncMock(return_value={
        "total_projects": 0,
        "status_distribution": {},
        "file_type_distribution": {},
        "storage_usage": {
            "total_size": 0,
            "average_size": 0,
            "file_count": 0
        }
    })

    service.search_projects = AsyncMock(return_value=([], 0))

    return service


@pytest.fixture
def mock_project_factory():
    """模拟项目工厂函数"""
    def create_mock_project(
        project_id="project-123",
        title="Test Project",
        description="Test description",
        status="active",
        file_type="txt",
        processing_status="completed"
    ):
        project = Mock()
        project.id = project_id
        project.title = title
        project.description = description
        project.status = status
        project.file_type = file_type
        project.file_processing_status = processing_status
        project.user_id = "test-user-123"
        project.file_size = 1024
        project.original_filename = "test.txt"
        project.minio_bucket = "test-bucket"
        project.minio_object_key = "uploads/test/test.txt"
        project.created_at = None
        project.updated_at = None
        project.processing_progress = 100.0
        project.task_id = None
        project.processing_error = None
        project.is_deleted = False
        project.deleted_at = None

        # 添加模型方法
        project.update_processing_progress = Mock()
        project.soft_delete = Mock()
        project.restore = Mock()
        project.is_valid_status = Mock(return_value=True)
        project.is_valid_file_type = Mock(return_value=True)
        project.is_valid_processing_status = Mock(return_value=True)

        return project

    return create_mock_project


# 测试标记配置
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试")


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为异步测试添加标记
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # 根据路径自动添加标记
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# 环境变量配置
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境变量"""
    # 设置测试环境变量
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "test-key")
    monkeypatch.setenv("MINIO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("MINIO_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")


# Mock配置
@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch):
    """设置通用mock"""
    # Mock外部服务
    monkeypatch.setattr("src.utils.storage.get_storage_client", lambda: AsyncMock())
    monkeypatch.setattr("src.services.project_service.get_project_service", lambda: AsyncMock())