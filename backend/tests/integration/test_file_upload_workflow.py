"""
文件上传完整工作流程集成测试
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.main import app
from src.core.database import get_db
from src.models.user import User
from src.models.project import Project, ProjectStatus, FileProcessingStatus, SupportedFileType
from src.services.project import ProjectService
from src.utils.storage import MinIOStorage


@pytest.mark.integration
class TestFileUploadWorkflow:
    """文件上传完整工作流程集成测试"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI

        # 使用依赖注入覆盖
        async def override_get_db():
            # 这里应该返回真实的测试数据库会话
            # 为了简化，我们使用mock
            mock_session = AsyncMock(spec=AsyncSession)
            return mock_session

        async def override_get_current_user():
            return User(
                id="test-user-id",
                email="test@example.com",
                name="Test User"
            )

        app.dependency_overrides[get_db] = override_get_db

        # 这里需要导入并覆盖认证依赖
        try:
            from src.core.auth0_auth import get_current_user
            app.dependency_overrides[get_current_user] = override_get_current_user
        except ImportError:
            pass

        yield TestClient(app)

        # 清理依赖覆盖
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_text_file(self):
        """创建测试文本文件"""
        content = """# 测试文档

这是一个测试文档内容。

## 第一章

第一章内容...

## 第二章

第二章内容...

包含一些测试数据：
- 项目1
- 项目2
- 项目3

这是文档的结尾。
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_markdown_file(self):
        """创建测试Markdown文件"""
        content = """# 测试Markdown文档

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
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    @patch('src.api.upload.get_project_service')
    @patch('src.api.upload.get_storage_client')
    async def test_complete_txt_file_upload_workflow(
        self, mock_get_storage, mock_get_service, client, sample_text_file
    ):
        """测试完整的TXT文件上传工作流程"""

        # Mock存储客户端
        mock_storage = AsyncMock(spec=MinIOStorage)
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/test-document.txt",
            "size": os.path.getsize(sample_text_file),
            "etag": "test-etag",
            "url": "http://minio-test-url/test-document.txt"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock(spec=ProjectService)
        mock_project = Mock(spec=Project)
        mock_project.id = "project-123"
        mock_project.title = "test-document.txt"
        mock_project.status = ProjectStatus.ACTIVE.value
        mock_project.file_processing_status = FileProcessingStatus.UPLOADED.value
        mock_service.create_project.return_value = mock_project
        mock_service.start_file_processing.return_value = True
        mock_service.get_processing_task_status.return_value = {
            "task_id": "task-123",
            "status": "processing",
            "result": None,
            "traceback": None
        }
        mock_get_service.return_value = mock_service

        # 1. 验证文件类型
        response = client.get("/api/v1/upload/validate-extension/test-document.txt")
        assert response.status_code == 200
        assert response.json()["valid"] is True

        # 2. 上传文件
        with open(sample_text_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload/single",
                files={"file": ("test-document.txt", f, "text/plain")},
                data={
                    "title": "测试文档",
                    "description": "这是一个测试文档的描述"
                }
            )

        assert response.status_code == 200
        upload_data = response.json()
        assert upload_data["success"] is True
        assert upload_data["project_id"] == "project-123"

        # 3. 检查项目创建参数
        mock_service.create_project.assert_called_once()
        create_call_args = mock_service.create_project.call_args
        assert create_call_args.kwargs["user_id"] == "test-user-id"
        assert create_call_args.kwargs["title"] == "测试文档"
        assert create_call_args.kwargs["description"] == "这是一个测试文档的描述"

        # 4. 检查文件上传参数
        mock_storage.upload_file.assert_called_once()

        # 5. 启动文件处理
        response = client.post("/api/v1/projects/project-123/process")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 6. 检查处理状态
        response = client.get("/api/v1/projects/project-123/processing-status")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["success"] is True
        assert status_data["task_status"]["status"] == "processing"

    @patch('src.api.upload.get_project_service')
    @patch('src.api.upload.get_storage_client')
    async def test_complete_markdown_file_upload_workflow(
        self, mock_get_storage, mock_get_service, client, sample_markdown_file
    ):
        """测试完整的Markdown文件上传工作流程"""

        # Mock存储客户端
        mock_storage = AsyncMock(spec=MinIOStorage)
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/test-guide.md",
            "size": os.path.getsize(sample_markdown_file),
            "etag": "md-etag",
            "url": "http://minio-test-url/test-guide.md"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock(spec=ProjectService)
        mock_project = Mock(spec=Project)
        mock_project.id = "project-456"
        mock_project.title = "test-guide.md"
        mock_project.file_type = SupportedFileType.MD.value
        mock_service.create_project.return_value = mock_project
        mock_get_service.return_value = mock_service

        # 上传Markdown文件
        with open(sample_markdown_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload/single",
                files={"file": ("test-guide.md", f, "text/markdown")},
                data={
                    "title": "测试指南",
                    "description": "Markdown格式的测试指南"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == "project-456"

        # 验证项目创建时包含了正确的文件类型
        create_call_args = mock_service.create_project.call_args
        assert create_call_args.kwargs["title"] == "测试指南"
        file_info = create_call_args.kwargs.get("file_info", {})
        assert file_info.get("file_type") == SupportedFileType.MD.value

    @patch('src.api.upload.get_project_service')
    @patch('src.api.upload.get_storage_client')
    async def test_multiple_files_upload_workflow(
        self, mock_get_storage, mock_get_service, client, sample_text_file, sample_markdown_file
    ):
        """测试多文件上传工作流程"""

        # Mock存储客户端
        mock_storage = AsyncMock(spec=MinIOStorage)
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/file",
            "size": 100,
            "etag": "multi-etag",
            "url": "http://minio-test-url/file"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock(spec=ProjectService)
        def create_project_side_effect(*args, **kwargs):
            mock_project = Mock(spec=Project)
            mock_project.id = f"project-{len(mock_service.create_project.call_args_list)}"
            mock_project.title = kwargs.get("title", "Untitled")
            return mock_project

        mock_service.create_project.side_effect = create_project_side_effect
        mock_get_service.return_value = mock_service

        # 准备多个文件
        files_data = []
        temp_files = []

        # TXT文件
        with open(sample_text_file, 'rb') as f:
            files_data.append(("files", ("document.txt", f.read(), "text/plain")))

        # MD文件
        with open(sample_markdown_file, 'rb') as f:
            files_data.append(("files", ("guide.md", f.read(), "text/markdown")))

        # 上传多个文件
        response = client.post(
            "/api/v1/upload/multiple",
            files=files_data,
            data={
                "titles": '["测试文档", "用户指南"]',
                "descriptions": '["文档描述", "指南描述"]'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 2

        # 验证每个文件都上传成功
        for result in data["results"]:
            assert result["success"] is True
            assert "project_id" in result

    @patch('src.api.upload.get_project_service')
    async def test_file_upload_error_handling(self, mock_get_service, client):
        """测试文件上传错误处理"""

        # Mock项目服务抛出异常
        mock_service = AsyncMock(spec=ProjectService)
        mock_service.create_project.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        # 创建测试文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/v1/upload/single",
                    files={"file": ("error-test.txt", f, "text/plain")},
                    data={"title": "错误测试"}
                )

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False

        finally:
            os.unlink(temp_path)

    @patch('src.api.upload.get_project_service')
    @patch('src.api.upload.get_storage_client')
    async def test_file_validation_workflow(
        self, mock_get_storage, mock_get_service, client
    ):
        """测试文件验证工作流程"""

        # 测试支持的文件类型
        supported_extensions = ['.txt', '.md', '.docx', '.epub']

        for ext in supported_extensions:
            response = client.get(f"/api/v1/upload/validate-extension/test{ext}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True

        # 测试不支持的文件类型
        unsupported_extensions = ['.pdf', '.exe', '.zip', '.jpg']

        for ext in unsupported_extensions:
            response = client.get(f"/api/v1/upload/validate-extension/test{ext}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False

    @patch('src.api.projects.get_project_service')
    @patch('src.api.files.get_storage_client')
    async def test_project_lifecycle_workflow(
        self, mock_get_storage, mock_get_service, client
    ):
        """测试项目生命周期工作流程"""

        # Mock项目
        mock_project = Mock(spec=Project)
        mock_project.id = "lifecycle-project"
        mock_project.title = "生命周期测试项目"
        mock_project.description = "测试项目生命周期"
        mock_project.status = ProjectStatus.ACTIVE.value
        mock_project.minio_bucket = "test-bucket"
        mock_project.minio_object_key = "uploads/test-user/lifecycle.txt"
        mock_project.original_filename = "lifecycle.txt"

        # Mock项目服务
        mock_service = AsyncMock(spec=ProjectService)
        mock_service.get_project_by_id.return_value = mock_project
        mock_service.get_user_projects.return_value = [mock_project]
        mock_service.update_project.return_value = mock_project
        mock_service.delete_project.return_value = True
        mock_service.restore_project.return_value = True
        mock_get_service.return_value = mock_service

        # Mock存储客户端
        mock_storage = AsyncMock(spec=MinIOStorage)
        mock_storage.get_file_info.return_value = {
            "object_key": "uploads/test-user/lifecycle.txt",
            "size": 1024,
            "url": "http://test-url"
        }
        mock_storage.delete_file.return_value = True
        mock_get_storage.return_value = mock_storage

        # 1. 创建项目（模拟）
        # 2. 获取项目详情
        response = client.get("/api/v1/projects/lifecycle-project")
        assert response.status_code == 200
        data = response.json()
        assert data["project"]["id"] == "lifecycle-project"

        # 3. 获取项目列表
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1

        # 4. 更新项目
        response = client.put(
            "/api/v1/projects/lifecycle-project",
            json={"title": "更新的项目标题", "description": "更新的描述"}
        )
        assert response.status_code == 200

        # 5. 获取文件信息
        response = client.get("/api/v1/files/lifecycle-project/info")
        assert response.status_code == 200

        # 6. 获取文件URL
        response = client.get("/api/v1/files/lifecycle-project/url")
        assert response.status_code == 200

        # 7. 软删除项目
        response = client.delete("/api/v1/projects/lifecycle-project")
        assert response.status_code == 200

        # 8. 恢复项目
        response = client.post("/api/v1/projects/lifecycle-project/restore")
        assert response.status_code == 200

        # 9. 永久删除项目
        response = client.delete("/api/v1/projects/lifecycle-project?permanent=true")
        assert response.status_code == 200

    @patch('src.api.projects.get_project_service')
    async def test_project_search_and_filter_workflow(self, mock_get_service, client):
        """测试项目搜索和过滤工作流程"""

        # Mock搜索结果
        mock_service = AsyncMock(spec=ProjectService)
        mock_service.search_projects.return_value = (
            [
                Mock(
                    id="search-result-1",
                    title="搜索测试项目1",
                    description="包含测试关键词的项目",
                    status=ProjectStatus.ACTIVE.value
                ),
                Mock(
                    id="search-result-2",
                    title="搜索测试项目2",
                    description="另一个测试项目",
                    status=ProjectStatus.COMPLETED.value
                )
            ],
            2  # 总数
        )

        mock_service.get_user_projects.return_value = [
            Mock(
                id="filtered-project",
                title="过滤测试项目",
                status=ProjectStatus.ACTIVE.value,
                file_type=SupportedFileType.TXT.value
            )
        ]
        mock_get_service.return_value = mock_service

        # 1. 搜索项目
        response = client.get("/api/v1/projects/search?q=测试&page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["projects"]) == 2
        assert data["total"] == 2

        # 2. 验证搜索调用参数
        search_call_args = mock_service.search_projects.call_args
        assert search_call_args.kwargs["query"] == "测试"
        assert search_call_args.kwargs["page"] == 1
        assert search_call_args.kwargs["size"] == 10

        # 3. 过滤项目列表
        response = client.get(
            "/api/v1/projects",
            params={
                "status": ProjectStatus.ACTIVE.value,
                "file_type": SupportedFileType.TXT.value,
                "search": "过滤"
            }
        )
        assert response.status_code == 200

        # 验证过滤调用参数
        list_call_args = mock_service.get_user_projects.call_args
        assert list_call_args.kwargs["status"] == ProjectStatus.ACTIVE
        assert list_call_args.kwargs["search"] == "过滤"


@pytest.mark.integration
class TestErrorHandlingWorkflow:
    """错误处理工作流程测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        async def override_get_db():
            return AsyncMock(spec=AsyncSession)

        async def override_get_current_user():
            return User(
                id="test-user-id",
                email="test@example.com",
                name="Test User"
            )

        app.dependency_overrides[get_db] = override_get_db

        try:
            from src.core.auth0_auth import get_current_user
            app.dependency_overrides[get_current_user] = override_get_current_user
        except ImportError:
            pass

        yield TestClient(app)
        app.dependency_overrides.clear()

    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        # 移除认证覆盖
        app.dependency_overrides.pop(get_current_user, None)

        # 尝试访问需要认证的端点
        response = client.get("/api/v1/projects")
        # 应该返回401或重定向到认证
        assert response.status_code in [401, 403, 307]

    async def test_validation_errors(self, client):
        """测试数据验证错误"""
        # 测试无效的项目创建数据
        response = client.post("/api/v1/projects", json={})
        assert response.status_code == 422

        # 测试无效的项目更新数据
        response = client.put("/api/v1/projects/test-id", json={"invalid_field": "value"})
        assert response.status_code == 422

    async def test_not_found_errors(self, client):
        """测试404错误"""
        # Mock服务返回None
        with patch('src.api.projects.get_project_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_project_by_id.return_value = None
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/projects/nonexistent")
            assert response.status_code == 404

    async def test_server_errors(self, client):
        """测试服务器错误"""
        # Mock服务抛出异常
        with patch('src.api.projects.get_project_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_user_projects.side_effect = Exception("Database connection failed")
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/projects")
            assert response.status_code == 500


if __name__ == '__main__':
    pytest.main([__file__])