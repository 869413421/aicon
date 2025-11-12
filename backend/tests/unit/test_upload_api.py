"""
上传API端点单元测试
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from src.api.upload import router
from src.core.auth0_auth import get_current_user
from src.core.database import get_db
from src.models.user import User
from src.models.project import SupportedFileType
from src.utils.file_handlers import FileProcessingError


class TestUploadAPI:
    """上传API测试"""

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
    def mock_user(self):
        """模拟用户"""
        return User(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )

    @pytest.fixture
    def sample_file(self):
        """创建测试文件"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is a test file content.")
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_validate_file_extension_valid(self, client):
        """测试有效文件扩展名验证"""
        response = client.get(
            "/api/v1/upload/validate-extension/test.txt"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["file_type"] == SupportedFileType.TXT.value

    def test_validate_file_extension_invalid(self, client):
        """测试无效文件扩展名验证"""
        response = client.get(
            "/api/v1/upload/validate-extension/test.xyz"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["file_type"] is None

    def test_validate_file_extension_empty(self, client):
        """测试空文件名验证"""
        response = client.get(
            "/api/v1/upload/validate-extension/"
        )
        assert response.status_code == 422

    @patch('src.api.upload.get_storage_client')
    @patch('src.api.upload.get_project_service')
    def test_upload_single_file_success(
        self, mock_get_service, mock_get_storage, client, sample_file
    ):
        """测试单文件上传成功"""
        # Mock存储客户端
        mock_storage = AsyncMock()
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/test.txt",
            "size": 100,
            "etag": "test-etag",
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.create_project.return_value = Mock(
            id="project-123",
            title="test.txt",
            file_processing_status="uploaded"
        )
        mock_get_service.return_value = mock_service

        # 上传文件
        with open(sample_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload/single",
                files={"file": ("test.txt", f, "text/plain")},
                data={"title": "Test Project"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == "project-123"
        assert data["message"] == "文件上传成功"

    @patch('src.api.upload.get_storage_client')
    def test_upload_single_file_storage_error(
        self, mock_get_storage, client, sample_file
    ):
        """测试存储错误"""
        mock_storage = AsyncMock()
        mock_storage.upload_file.side_effect = Exception("Storage error")
        mock_get_storage.return_value = mock_storage

        with open(sample_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload/single",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "存储错误" in data["message"]

    def test_upload_single_file_no_file(self, client):
        """测试未提供文件"""
        response = client.post("/api/v1/upload/single")
        assert response.status_code == 422

    def test_upload_single_file_invalid_type(self, client):
        """测试无效文件类型"""
        # 创建一个不支持的文件类型
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"Fake PDF content")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/v1/upload/single",
                    files={"file": ("test.pdf", f, "application/pdf")}
                )
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "不支持的文件类型" in data["message"]
        finally:
            os.unlink(temp_path)

    @patch('src.api.upload.get_storage_client')
    @patch('src.api.upload.get_project_service')
    def test_upload_multiple_files_success(
        self, mock_get_service, mock_get_storage, client
    ):
        """测试多文件上传成功"""
        # Mock存储客户端
        mock_storage = AsyncMock()
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/test.txt",
            "size": 100,
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.create_project.return_value = Mock(id="project-123")
        mock_get_service.return_value = mock_service

        # 创建测试文件
        files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(f"Test file {i} content".encode())
                temp_path = f.name
                files.append(temp_path)

        try:
            # 准备文件列表
            upload_files = [
                ("files", (f"test{i}.txt", open(files[i], 'rb'), "text/plain"))
                for i in range(2)
            ]

            response = client.post(
                "/api/v1/upload/multiple",
                files=upload_files,
                data={"titles": '["Test Project 1", "Test Project 2"]'}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["results"]) == 2
            assert all(result["success"] for result in data["results"])

        finally:
            # 清理临时文件
            for f in upload_files:
                f[1][1].close()
            for temp_path in files:
                os.unlink(temp_path)

    def test_get_upload_status_no_task_id(self, client):
        """测试获取上传状态未提供任务ID"""
        response = client.get("/api/v1/upload/status")
        assert response.status_code == 422

    @patch('src.api.upload.get_project_service')
    def test_get_upload_status_success(self, mock_get_service, client):
        """测试获取上传状态成功"""
        mock_service = AsyncMock()
        mock_service.get_processing_task_status.return_value = {
            "task_id": "task-123",
            "status": "processing",
            "result": None,
            "traceback": None
        }
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/upload/status?task_id=task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["task_status"]["status"] == "processing"

    @patch('src.api.upload.get_project_service')
    def test_get_upload_status_not_found(self, mock_get_service, client):
        """测试获取上传状态任务不存在"""
        mock_service = AsyncMock()
        mock_service.get_processing_task_status.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/upload/status?task_id=nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "任务不存在" in data["message"]

    def test_get_file_types(self, client):
        """测试获取支持的文件类型"""
        response = client.get("/api/v1/upload/file-types")
        assert response.status_code == 200
        data = response.json()
        assert "supported_types" in data
        assert len(data["supported_types"]) > 0

    @patch('src.api.upload.get_storage_client')
    def test_get_presigned_url_success(self, mock_get_storage, client):
        """测试获取预签名URL成功"""
        mock_storage = AsyncMock()
        mock_storage.get_presigned_url.return_value = "http://presigned-url.com/file"
        mock_get_storage.return_value = mock_storage

        response = client.get(
            "/api/v1/upload/presigned-url",
            params={"object_key": "uploads/test/file.txt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "http://presigned-url.com/file"

    def test_get_presigned_url_no_object_key(self, client):
        """测试获取预签名URL未提供对象键"""
        response = client.get("/api/v1/upload/presigned-url")
        assert response.status_code == 422

    @patch('src.api.upload.get_storage_client')
    def test_get_presigned_url_error(self, mock_get_storage, client):
        """测试获取预签名URL错误"""
        mock_storage = AsyncMock()
        mock_storage.get_presigned_url.side_effect = Exception("URL generation failed")
        mock_get_storage.return_value = mock_storage

        response = client.get(
            "/api/v1/upload/presigned-url",
            params={"object_key": "uploads/test/file.txt"}
        )
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('src.api.upload.get_storage_client')
    def test_delete_file_success(self, mock_get_storage, client):
        """测试删除文件成功"""
        mock_storage = AsyncMock()
        mock_storage.delete_file.return_value = True
        mock_get_storage.return_value = mock_storage

        response = client.delete(
            "/api/v1/upload/file",
            params={"object_key": "uploads/test/file.txt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "文件删除成功"

    def test_delete_file_no_object_key(self, client):
        """测试删除文件未提供对象键"""
        response = client.delete("/api/v1/upload/file")
        assert response.status_code == 422

    @patch('src.api.upload.get_storage_client')
    def test_delete_file_error(self, mock_get_storage, client):
        """测试删除文件错误"""
        mock_storage = AsyncMock()
        mock_storage.delete_file.side_effect = Exception("Delete failed")
        mock_get_storage.return_value = mock_storage

        response = client.delete(
            "/api/v1/upload/file",
            params={"object_key": "uploads/test/file.txt"}
        )
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    def test_chunk_upload_init_no_filename(self, client):
        """测试初始化分块上传未提供文件名"""
        response = client.post("/api/v1/upload/chunk/init")
        assert response.status_code == 422

    @patch('src.api.upload.get_storage_client')
    def test_chunk_upload_init_success(self, mock_get_storage, client):
        """测试初始化分块上传成功"""
        mock_storage = AsyncMock()
        mock_storage.initiate_multipart_upload.return_value = {
            "upload_id": "upload-123",
            "key": "uploads/test/file.txt"
        }
        mock_get_storage.return_value = mock_storage

        response = client.post(
            "/api/v1/upload/chunk/init",
            params={"filename": "test.txt", "total_size": 1000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["upload_id"] == "upload-123"

    def test_chunk_upload_no_upload_id(self, client):
        """测试分块上传未提供上传ID"""
        response = client.post("/api/v1/upload/chunk")
        assert response.status_code == 422


class TestUploadAPIIntegration:
    """上传API集成测试"""

    @patch('src.api.upload.get_storage_client')
    @patch('src.api.upload.get_project_service')
    @patch('src.api.upload.file_validator')
    def test_complete_upload_workflow(
        self, mock_validator, mock_get_service, mock_get_storage
    ):
        """测试完整上传工作流程"""
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

        # Mock验证器
        mock_validator.validate_file.return_value = {
            "is_supported": True,
            "file_type": SupportedFileType.TXT,
            "file_size": 100
        }

        # Mock存储
        mock_storage = AsyncMock()
        mock_storage.upload_file.return_value = {
            "success": True,
            "bucket": "test-bucket",
            "object_key": "uploads/test-user/test.txt",
            "size": 100,
            "etag": "test-etag",
            "url": "http://test-url"
        }
        mock_get_storage.return_value = mock_storage

        # Mock项目服务
        mock_service = AsyncMock()
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_service.create_project.return_value = mock_project
        mock_service.start_file_processing.return_value = True
        mock_get_service.return_value = mock_service

        # 1. 验证文件类型
        response = client.get("/api/v1/upload/validate-extension/test.txt")
        assert response.json()["valid"] is True

        # 2. 创建测试文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content for workflow")
            temp_path = f.name

        try:
            # 3. 上传文件
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/v1/upload/single",
                    files={"file": ("test.txt", f, "text/plain")},
                    data={"title": "Workflow Test", "description": "Test description"}
                )

            assert response.status_code == 200
            upload_data = response.json()
            assert upload_data["success"] is True
            assert upload_data["project_id"] == "project-123"

            # 4. 检查项目创建
            mock_service.create_project.assert_called_once()

        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__])