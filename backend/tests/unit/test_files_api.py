"""
文件管理API端点单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from src.api.files import router
from src.core.auth0_auth import get_current_user
from src.core.database import get_db
from src.models.user import User
from src.models.project import Project, SupportedFileType


class TestFilesAPI:
    """文件管理API测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Mock依赖注入
        app.dependency_overrides[get_current_user] = lambda: User(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        return TestClient(app)

    @pytest.fixture
    def mock_project(self):
        """模拟项目"""
        project = Mock(spec=Project)
        project.id = "project-123"
        project.title = "Test Project"
        project.minio_bucket = "test-bucket"
        project.minio_object_key = "uploads/test-user/test.txt"
        project.original_filename = "test.txt"
        project.file_type = SupportedFileType.TXT.value
        project.file_size = 1024
        return project

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_info_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取文件信息成功"""
        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        # Mock存储客户端
        mock_storage = AsyncMock()
        mock_storage.get_file_info.return_value = {
            "object_key": "uploads/test-user/test.txt",
            "size": 1024,
            "last_modified": datetime.now(),
            "etag": "test-etag",
            "content_type": "text/plain",
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files/project-123/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_info"]["object_key"] == "uploads/test-user/test.txt"
        assert data["file_info"]["size"] == 1024

    @patch('src.api.files.get_project_service')
    def test_get_file_info_project_not_found(self, mock_get_service, client):
        """测试获取文件信息项目不存在"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/files/nonexistent/info")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "项目不存在" in data["message"]

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_info_no_storage_file(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取文件信息项目无存储文件"""
        mock_project.minio_object_key = None

        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/files/project-123/info")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "项目没有关联的文件" in data["message"]

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_download_file_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试下载文件成功"""
        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        # Mock存储客户端
        mock_storage = AsyncMock()
        test_content = b"This is test file content"
        mock_storage.download_file.return_value = test_content
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files/project-123/download")
        assert response.status_code == 200
        assert response.content == test_content
        assert response.headers["content-disposition"] == 'attachment; filename="test.txt"'

    @patch('src.api.files.get_project_service')
    def test_download_file_project_not_found(self, mock_get_service, client):
        """测试下载文件项目不存在"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/files/nonexistent/download")
        assert response.status_code == 404

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_download_file_storage_error(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试下载文件存储错误"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.download_file.side_effect = Exception("Download failed")
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files/project-123/download")
        assert response.status_code == 500

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_url_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取文件URL成功"""
        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        # Mock存储客户端
        mock_storage = AsyncMock()
        mock_storage.get_presigned_url.return_value = "http://presigned-url.com/file"
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files/project-123/url")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "http://presigned-url.com/file"

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_url_with_expiry(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取带过期时间的文件URL"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.get_presigned_url.return_value = "http://presigned-url.com/file"
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files/project-123/url?expires_in=7200")
        assert response.status_code == 200

        # 验证调用参数
        mock_storage.get_presigned_url.assert_called_once()

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_delete_file_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试删除文件成功"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_service.update_project.return_value = mock_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.delete_file.return_value = True
        mock_get_storage.return_value = mock_storage

        response = client.delete("/api/v1/files/project-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "文件删除成功"

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_delete_file_storage_error(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试删除文件存储错误"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.delete_file.return_value = False
        mock_get_storage.return_value = mock_storage

        response = client.delete("/api/v1/files/project-123")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_copy_file_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试复制文件成功"""
        # Mock目标项目
        target_project = Mock(spec=Project)
        target_project.id = "target-456"
        target_project.minio_bucket = "test-bucket"

        mock_service = AsyncMock()
        mock_service.get_project_by_id.side_effect = [mock_project, target_project]
        mock_service.update_project.return_value = target_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.copy_file.return_value = True
        mock_get_storage.return_value = mock_storage

        response = client.post(
            "/api/v1/files/project-123/copy",
            json={"target_project_id": "target-456"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "文件复制成功"

    @patch('src.api.files.get_project_service')
    def test_copy_file_same_project(self, mock_get_service, client, mock_project):
        """测试复制文件到同一项目"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/files/project-123/copy",
            json={"target_project_id": "project-123"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "不能复制到同一项目" in data["message"]

    @patch('src.api.files.get_project_service')
    def test_copy_file_no_target_project(self, mock_get_service, client):
        """测试复制文件未提供目标项目"""
        response = client.post("/api/v1/files/project-123/copy", json={})
        assert response.status_code == 422

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_move_file_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试移动文件成功"""
        # Mock目标项目
        target_project = Mock(spec=Project)
        target_project.id = "target-456"
        target_project.minio_bucket = "test-bucket"

        mock_service = AsyncMock()
        mock_service.get_project_by_id.side_effect = [mock_project, target_project]
        mock_service.update_project.return_value = target_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.copy_file.return_value = True
        mock_storage.delete_file.return_value = True
        mock_get_storage.return_value = mock_storage

        response = client.post(
            "/api/v1/files/project-123/move",
            json={"target_project_id": "target-456"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "文件移动成功"

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_list_user_files_success(self, mock_get_storage, mock_get_service, client):
        """测试列出用户文件成功"""
        mock_service = AsyncMock()
        mock_service.get_user_projects.return_value = [
            Mock(
                id="project-1",
                minio_object_key="uploads/test-user/file1.txt",
                original_filename="file1.txt",
                file_type=SupportedFileType.TXT.value
            ),
            Mock(
                id="project-2",
                minio_object_key="uploads/test-user/file2.md",
                original_filename="file2.md",
                file_type=SupportedFileType.MD.value
            )
        ]
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        mock_storage.get_file_info.return_value = {
            "object_key": "uploads/test-user/file1.txt",
            "size": 1024,
            "last_modified": datetime.now(),
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        response = client.get("/api/v1/files")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["files"]) == 2

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_list_user_files_with_filters(self, mock_get_storage, mock_get_service, client):
        """测试带过滤条件列出用户文件"""
        mock_service = AsyncMock()
        mock_service.get_user_projects.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/files",
            params={
                "file_type": SupportedFileType.TXT.value,
                "page": 2,
                "size": 5,
                "search": "test"
            }
        )
        assert response.status_code == 200

        # 验证调用参数
        call_args = mock_service.get_user_projects.call_args
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["size"] == 5
        assert call_args.kwargs["search"] == "test"

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_preview_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取文件预览成功"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        # Mock存储客户端和文件处理器
        mock_storage = AsyncMock()
        test_content = b"This is test file content for preview"
        mock_storage.download_file.return_value = test_content
        mock_get_storage.return_value = mock_storage

        with patch('src.api.files.get_file_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.get_preview.return_value = {
                "content": "This is test file content for preview",
                "preview_type": "text",
                "metadata": {
                    "word_count": 8,
                    "char_count": 33,
                    "line_count": 1
                }
            }
            mock_get_handler.return_value = mock_handler

            response = client.get("/api/v1/files/project-123/preview")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["preview"]["content"] == "This is test file content for preview"
            assert data["preview"]["preview_type"] == "text"

    @patch('src.api.files.get_project_service')
    def test_get_file_preview_unsupported_type(self, mock_get_service, client, mock_project):
        """测试获取不支持的文件类型预览"""
        mock_project.file_type = SupportedFileType.EPUB.value

        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/files/project-123/preview")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "不支持预览的文件类型" in data["message"]

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_get_file_analytics_success(self, mock_get_storage, mock_get_service, client, mock_project):
        """测试获取文件分析成功"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        test_content = b"This is test file content for analytics"
        mock_storage.download_file.return_value = test_content
        mock_get_storage.return_value = mock_storage

        with patch('src.api.files.get_file_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.analyze_content.return_value = {
                "word_count": 8,
                "char_count": 38,
                "line_count": 1,
                "paragraph_count": 1,
                "sentence_count": 1,
                "readability_score": 85.5,
                "language": "en",
                "keywords": ["test", "file", "content", "analytics"]
            }
            mock_get_handler.return_value = mock_handler

            response = client.get("/api/v1/files/project-123/analytics")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["analytics"]["word_count"] == 8
            assert "keywords" in data["analytics"]

    def test_get_file_analytics_project_not_found(self, client):
        """测试获取文件分析项目不存在"""
        with patch('src.api.files.get_project_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_project_by_id.return_value = None
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/files/nonexistent/analytics")
            assert response.status_code == 404


class TestFilesAPIIntegration:
    """文件管理API集成测试"""

    @patch('src.api.files.get_project_service')
    @patch('src.api.files.get_storage_client')
    def test_complete_file_workflow(self, mock_get_storage, mock_get_service):
        """测试完整文件工作流程"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Mock依赖
        app.dependency_overrides[get_current_user] = lambda: User(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        client = TestClient(app)

        # Mock项目
        mock_project = Mock(spec=Project)
        mock_project.id = "project-123"
        mock_project.minio_bucket = "test-bucket"
        mock_project.minio_object_key = "uploads/test-user/test.txt"
        mock_project.original_filename = "test.txt"
        mock_project.file_type = SupportedFileType.TXT.value
        mock_project.file_size = 1024

        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_service.get_user_projects.return_value = [mock_project]
        mock_get_service.return_value = mock_service

        mock_storage = AsyncMock()
        test_content = b"This is test file content"
        mock_storage.download_file.return_value = test_content
        mock_storage.get_presigned_url.return_value = "http://presigned-url.com/file"
        mock_storage.get_file_info.return_value = {
            "object_key": "uploads/test-user/test.txt",
            "size": 1024,
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        # 1. 获取文件信息
        info_response = client.get("/api/v1/files/project-123/info")
        assert info_response.status_code == 200
        info_data = info_response.json()
        assert info_data["success"] is True

        # 2. 获取文件URL
        url_response = client.get("/api/v1/files/project-123/url")
        assert url_response.status_code == 200
        url_data = url_response.json()
        assert url_data["success"] is True

        # 3. 下载文件
        download_response = client.get("/api/v1/files/project-123/download")
        assert download_response.status_code == 200
        assert download_response.content == test_content

        # 4. 列出用户文件
        list_response = client.get("/api/v1/files")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert len(list_data["files"]) == 1


if __name__ == '__main__':
    pytest.main([__file__])