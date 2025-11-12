"""
存储服务单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.utils.storage import MinIOStorage, StorageError
from src.core.config import settings


class TestMinIOStorage:
    """MinIO存储服务测试"""

    @pytest.fixture
    def storage_client(self):
        """创建存储客户端实例"""
        with patch('src.utils.storage.Minio') as mock_minio:
            mock_client = Mock()
            mock_minio.return_value = mock_client

            storage = MinIOStorage()
            storage.client = mock_client
            return storage, mock_client

    @pytest.fixture
    def sample_file(self):
        """创建示例文件"""
        content = b"This is a test file content for storage testing."
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def mock_upload_file(self):
        """模拟上传文件对象"""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.file = Mock()
        mock_file.file.seek = Mock()
        mock_file.file.tell = Mock()
        mock_file.file.read = Mock(return_value=b"test content")
        mock_file.file.seek.return_value = 0
        return mock_file

    def test_init_storage(self, storage_client):
        """测试存储客户端初始化"""
        storage, mock_client = storage_client

        assert storage.client == mock_client
        assert storage.bucket_name == settings.MINIO_BUCKET_NAME

    @patch('src.utils.storage.get_storage_client')
    async def test_ensure_bucket_exists_new(self, mock_get_storage):
        """测试确保存储桶存在（新存储桶）"""
        mock_storage = AsyncMock()
        mock_storage.client.bucket_exists.return_value = False
        mock_storage.client.make_bucket.return_value = None
        mock_get_storage.return_value = mock_storage

        await mock_storage.ensure_bucket_exists()

        mock_storage.client.bucket_exists.assert_called_once()
        mock_storage.client.make_bucket.assert_called_once()

    @patch('src.utils.storage.get_storage_client')
    async def test_ensure_bucket_exists_existing(self, mock_get_storage):
        """测试确保存储桶存在（已存在）"""
        mock_storage = AsyncMock()
        mock_storage.client.bucket_exists.return_value = True
        mock_get_storage.return_value = mock_storage

        await mock_storage.ensure_bucket_exists()

        mock_storage.client.bucket_exists.assert_called_once()
        mock_storage.client.make_bucket.assert_not_called()

    @patch('src.utils.storage.get_storage_client')
    async def test_ensure_bucket_exists_error(self, mock_get_storage):
        """测试确保存储桶存在（错误情况）"""
        mock_storage = AsyncMock()
        mock_storage.client.bucket_exists.side_effect = Exception("Connection error")
        mock_get_storage.return_value = mock_storage

        with pytest.raises(StorageError):
            await mock_storage.ensure_bucket_exists()

    def test_generate_object_key(self, storage_client):
        """测试生成对象键"""
        storage, _ = storage_client

        user_id = "user123"
        filename = "test.txt"

        object_key = storage.generate_object_key(user_id, filename)

        assert object_key.startswith("uploads/user123/")
        assert object_key.endswith(".txt")
        assert "test" in object_key

    def test_generate_object_key_with_prefix(self, storage_client):
        """测试生成对象键（带前缀）"""
        storage, _ = storage_client

        user_id = "user123"
        filename = "test.txt"
        prefix = "documents"

        object_key = storage.generate_object_key(user_id, filename, prefix)

        assert object_key.startswith(f"{prefix}/user123/")
        assert object_key.endswith(".txt")

    @patch('src.utils.storage.get_storage_client')
    async def test_upload_file_success(self, mock_get_storage, sample_file, mock_upload_file):
        """测试文件上传成功"""
        mock_storage = AsyncMock()
        mock_storage.bucket_name = "test-bucket"

        # Mock bucket exists
        mock_storage.client.bucket_exists.return_value = True

        # Mock put_object result
        mock_result = Mock()
        mock_result.etag = "test-etag"
        mock_storage.client.put_object.return_value = mock_result

        # Mock presigned URL
        mock_storage.client.presigned_get_object.return_value = "http://test-url"

        mock_get_storage.return_value = mock_storage

        # 准备文件内容
        with open(sample_file, 'rb') as f:
            file_content = f.read()

        # 修改mock_upload_file以返回正确的内容
        mock_upload_file.file.seek.return_value = 0
        mock_upload_file.file.tell.return_value = len(file_content)
        mock_upload_file.file.read.return_value = file_content

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.upload_file("user123", mock_upload_file)

        assert result['success'] is True
        assert result['bucket'] == "test-bucket"
        assert result['object_key'].startswith("uploads/user123/")
        assert result['size'] == len(file_content)
        assert result['etag'] == "test-etag"
        assert 'url' in result

    @patch('src.utils.storage.get_storage_client')
    async def test_upload_file_error(self, mock_get_storage, mock_upload_file):
        """测试文件上传失败"""
        mock_storage = AsyncMock()
        mock_storage.client.bucket_exists.return_value = True
        mock_storage.client.put_object.side_effect = Exception("Upload failed")
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        with pytest.raises(StorageError):
            await storage.upload_file("user123", mock_upload_file)

    @patch('src.utils.storage.get_storage_client')
    async def test_download_file_success(self, mock_get_storage):
        """测试文件下载成功"""
        mock_storage = AsyncMock()
        test_content = b"Downloaded file content"
        mock_response = Mock()
        mock_response.read.return_value = test_content
        mock_storage.client.get_object.return_value = mock_response
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.download_file("test-object-key")

        assert result == test_content
        mock_storage.client.get_object.assert_called_once_with("test-bucket", "test-object-key")

    @patch('src.utils.storage.get_storage_client')
    async def test_download_file_error(self, mock_get_storage):
        """测试文件下载失败"""
        mock_storage = AsyncMock()
        mock_storage.client.get_object.side_effect = Exception("Download failed")
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        with pytest.raises(StorageError):
            await storage.download_file("test-object-key")

    @patch('src.utils.storage.get_storage_client')
    async def test_delete_file_success(self, mock_get_storage):
        """测试文件删除成功"""
        mock_storage = AsyncMock()
        mock_storage.client.remove_object.return_value = None
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.delete_file("test-object-key")

        assert result is True
        mock_storage.client.remove_object.assert_called_once_with("test-bucket", "test-object-key")

    @patch('src.utils.storage.get_storage_client')
    async def test_delete_file_error(self, mock_get_storage):
        """测试文件删除失败"""
        mock_storage = AsyncMock()
        mock_storage.client.remove_object.side_effect = Exception("Delete failed")
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.delete_file("test-object-key")

        assert result is False

    @patch('src.utils.storage.get_storage_client')
    async def test_get_presigned_url(self, mock_get_storage):
        """测试获取预签名URL"""
        mock_storage = AsyncMock()
        mock_url = "http://presigned-url.com/file"
        mock_storage.client.presigned_get_object.return_value = mock_url
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = storage.get_presigned_url("test-object-key")

        assert result == mock_url
        mock_storage.client.presigned_get_object.assert_called_once()

    @patch('src.utils.storage.get_storage_client')
    async def test_get_presigned_url_error(self, mock_get_storage):
        """测试获取预签名URL失败"""
        mock_storage = AsyncMock()
        mock_storage.client.presigned_get_object.side_effect = Exception("URL generation failed")
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        with pytest.raises(StorageError):
            storage.get_presigned_url("test-object-key")

    @patch('src.utils.storage.get_storage_client')
    async def test_list_files(self, mock_get_storage):
        """测试列出文件"""
        mock_storage = AsyncMock()
        mock_objects = []

        # 创建模拟对象
        for i in range(3):
            mock_obj = Mock()
            mock_obj.object_name = f"uploads/user123/file{i}.txt"
            mock_obj.size = 1024 * (i + 1)
            mock_obj.last_modified = datetime.now()
            mock_obj.etag = f"etag-{i}"
            mock_obj.content_type = "text/plain"
            mock_objects.append(mock_obj)

        mock_client = Mock()
        mock_client.list_objects.return_value = mock_objects
        mock_storage.client = mock_client
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_client
        storage.bucket_name = "test-bucket"

        result = await storage.list_files("uploads/user123/", limit=10)

        assert len(result) == 3
        assert all('object_key' in item for item in result)
        assert all('size' in item for item in result)
        assert all('url' in item for item in result)

    @patch('src.utils.storage.get_storage_client')
    async def test_get_file_info(self, mock_get_storage):
        """测试获取文件信息"""
        mock_storage = AsyncMock()
        mock_stat = Mock()
        mock_stat.size = 2048
        mock_stat.last_modified = datetime.now()
        mock_stat.etag = "test-etag"
        mock_stat.content_type = "text/plain"
        mock_stat.metadata = {"user_id": "user123"}
        mock_storage.client.stat_object.return_value = mock_stat
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.get_file_info("test-object-key")

        assert result is not None
        assert result['object_key'] == "test-object-key"
        assert result['size'] == 2048
        assert result['etag'] == "test-etag"
        assert 'url' in result

    @patch('src.utils.storage.get_storage_client')
    async def test_get_file_info_not_found(self, mock_get_storage):
        """测试获取不存在的文件信息"""
        mock_storage = AsyncMock()
        from minio.error import S3Error
        mock_storage.client.stat_object.side_effect = S3Error("Not found", "NoSuchKey", "")
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.get_file_info("nonexistent-object-key")

        assert result is None

    @patch('src.utils.storage.get_storage_client')
    async def test_file_exists(self, mock_get_storage):
        """测试检查文件是否存在"""
        mock_storage = AsyncMock()
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client

        # 文件存在
        mock_storage.client.stat_object.return_value = Mock()
        assert await storage.file_exists("existing-file") is True

        # 文件不存在
        from minio.error import S3Error
        mock_storage.client.stat_object.side_effect = S3Error("Not found", "NoSuchKey", "")
        assert await storage.file_exists("nonexistent-file") is False

    @patch('src.utils.storage.get_storage_client')
    async def test_upload_file_from_path(self, mock_get_storage, sample_file):
        """测试从路径上传文件"""
        mock_storage = AsyncMock()
        mock_storage.bucket_name = "test-bucket"
        mock_storage.client.bucket_exists.return_value = True

        mock_result = Mock()
        mock_result.etag = "path-etag"
        mock_storage.client.put_object.return_value = mock_result
        mock_storage.client.presigned_get_object.return_value = "http://test-url"

        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.upload_file_from_path(
            user_id="user123",
            file_path=sample_file,
            original_filename="test.txt"
        )

        assert result['success'] is True
        assert result['bucket'] == "test-bucket"
        assert result['size'] > 0
        assert 'url' in result

    @patch('src.utils.storage.get_storage_client')
    async def test_copy_file(self, mock_get_storage):
        """测试复制文件"""
        mock_storage = AsyncMock()
        mock_storage.bucket_name = "test-bucket"
        mock_storage.client.copy_object.return_value = Mock()
        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        result = await storage.copy_file(
            source_object_key="source-file.txt",
            dest_object_key="dest-file.txt"
        )

        assert result is True
        mock_storage.client.copy_object.assert_called_once()


class TestStorageIntegration:
    """存储服务集成测试"""

    @patch('src.utils.storage.get_storage_client')
    async def test_complete_file_lifecycle(self, mock_get_storage):
        """测试完整的文件生命周期"""
        # 模拟存储客户端
        mock_storage = AsyncMock()
        mock_storage.bucket_name = "test-bucket"
        mock_storage.client.bucket_exists.return_value = True

        # Mock文件对象
        mock_file = Mock()
        mock_file.filename = "lifecycle-test.txt"
        mock_file.content_type = "text/plain"
        mock_file.file = Mock()
        mock_file.file.seek = Mock(return_value=0)
        mock_file.file.tell = Mock(return_value=50)
        mock_file.file.read = Mock(return_value=b"Lifecycle test content")

        # Mock上传
        mock_result = Mock()
        mock_result.etag = "lifecycle-etag"
        mock_storage.client.put_object.return_value = mock_result

        # Mock下载
        mock_response = Mock()
        mock_response.read.return_value = b"Lifecycle test content"
        mock_storage.client.get_object.return_value = mock_response

        # Mock删除
        mock_storage.client.remove_object.return_value = None

        # Mock其他操作
        mock_storage.client.stat_object.return_value = Mock()
        mock_storage.client.presigned_get_object.return_value = "http://test-url"
        mock_storage.client.list_objects.return_value = []

        mock_get_storage.return_value = mock_storage

        storage = MinIOStorage()
        storage.client = mock_storage.client
        storage.bucket_name = "test-bucket"

        # 1. 上传文件
        upload_result = await storage.upload_file("user123", mock_file)
        assert upload_result['success'] is True
        object_key = upload_result['object_key']

        # 2. 检查文件是否存在
        assert await storage.file_exists(object_key) is True

        # 3. 获取文件信息
        file_info = await storage.get_file_info(object_key)
        assert file_info is not None

        # 4. 下载文件
        downloaded_content = await storage.download_file(object_key)
        assert downloaded_content == b"Lifecycle test content"

        # 5. 获取预签名URL
        presigned_url = storage.get_presigned_url(object_key)
        assert presigned_url == "http://test-url"

        # 6. 删除文件
        delete_result = await storage.delete_file(object_key)
        assert delete_result is True

        # 7. 确认文件已被删除
        mock_storage.client.stat_object.side_effect = Exception("Not found")
        assert await storage.file_exists(object_key) is False


if __name__ == '__main__':
    pytest.main([__file__])