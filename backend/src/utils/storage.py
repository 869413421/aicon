"""
MinIO对象存储客户端 - 文件存储和管理
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any, List
from urllib.parse import urljoin

import aiofiles
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, UploadFile

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class StorageError(Exception):
    """存储异常"""
    pass


class MinIOStorage:
    """MinIO对象存储客户端"""

    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

    async def ensure_bucket_exists(self) -> None:
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name, location="us-east-1")
                logger.info(f"创建MinIO存储桶: {self.bucket_name}")

                # 设置存储桶策略（可选）
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/public/*"]
                        }
                    ]
                }
                # 注意：实际环境中可能需要更严格的权限控制
        except S3Error as e:
            logger.error(f"创建MinIO存储桶失败: {e}")
            raise StorageError(f"无法创建存储桶: {str(e)}")

    def generate_object_key(self, user_id: str, filename: str, prefix: str = "uploads") -> str:
        """
        生成对象键

        Args:
            user_id: 用户ID
            filename: 文件名
            prefix: 前缀

        Returns:
            对象键路径
        """
        # 生成唯一文件名
        file_ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{file_ext}"

        # 构建路径: uploads/user_id/date/unique_name
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{prefix}/{user_id}/{date_str}/{unique_name}"

    async def upload_file(
        self,
        user_id: str,
        file: UploadFile,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        上传文件到MinIO

        Args:
            user_id: 用户ID
            file: 上传的文件
            object_key: 对象键（可选，自动生成）
            metadata: 文件元数据

        Returns:
            上传结果信息
        """
        try:
            await self.ensure_bucket_exists()

            if not object_key:
                object_key = self.generate_object_key(user_id, file.filename)

            # 准备元数据
            if metadata is None:
                metadata = {}

            metadata.update({
                "original_filename": file.filename or "",
                "content_type": file.content_type or "application/octet-stream",
                "upload_time": datetime.now().isoformat(),
                "user_id": user_id,
            })

            # 重置文件指针
            file.file.seek(0)

            # 获取文件大小
            file.file.seek(0, 2)  # 移动到末尾
            file_size = file.file.tell()
            file.file.seek(0)  # 重置到开头

            # 上传文件
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=file.file,
                length=file_size,
                content_type=file.content_type,
                metadata=metadata,
            )

            logger.info(f"文件上传成功: {object_key}, 大小: {file_size} bytes")

            return {
                "bucket": self.bucket_name,
                "object_key": object_key,
                "size": file_size,
                "etag": result.etag,
                "url": self.get_presigned_url(object_key),
            }

        except S3Error as e:
            logger.error(f"MinIO上传失败: {e}")
            raise StorageError(f"文件上传失败: {str(e)}")
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            raise StorageError(f"文件上传异常: {str(e)}")

    async def upload_file_from_path(
        self,
        user_id: str,
        file_path: str,
        original_filename: str,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        从本地路径上传文件到MinIO

        Args:
            user_id: 用户ID
            file_path: 本地文件路径
            original_filename: 原始文件名
            object_key: 对象键（可选）
            metadata: 文件元数据

        Returns:
            上传结果信息
        """
        try:
            if not object_key:
                object_key = self.generate_object_key(user_id, original_filename)

            if metadata is None:
                metadata = {}

            # 获取文件大小
            file_size = Path(file_path).stat().st_size

            # 准备元数据
            metadata.update({
                "original_filename": original_filename,
                "content_type": "application/octet-stream",
                "upload_time": datetime.now().isoformat(),
                "user_id": user_id,
                "file_path": file_path,
            })

            # 上传文件
            with open(file_path, 'rb') as file_data:
                result = self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_key,
                    data=file_data,
                    length=file_size,
                    metadata=metadata,
                )

            logger.info(f"文件上传成功: {object_key}, 大小: {file_size} bytes")

            return {
                "bucket": self.bucket_name,
                "object_key": object_key,
                "size": file_size,
                "etag": result.etag,
                "url": self.get_presigned_url(object_key),
            }

        except S3Error as e:
            logger.error(f"MinIO上传失败: {e}")
            raise StorageError(f"文件上传失败: {str(e)}")
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            raise StorageError(f"文件上传异常: {str(e)}")

    def get_presigned_url(
        self,
        object_key: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        获取预签名URL

        Args:
            object_key: 对象键
            expires: 过期时间

        Returns:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(f"获取预签名URL失败: {e}")
            raise StorageError(f"获取预签名URL失败: {str(e)}")

    async def download_file(self, object_key: str) -> bytes:
        """
        下载文件

        Args:
            object_key: 对象键

        Returns:
            文件内容
        """
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            return response.read()
        except S3Error as e:
            logger.error(f"下载文件失败: {e}")
            raise StorageError(f"下载文件失败: {str(e)}")

    async def download_file_to_path(self, object_key: str, dest_path: str) -> None:
        """
        下载文件到指定路径

        Args:
            object_key: 对象键
            dest_path: 目标路径
        """
        try:
            response = self.client.get_object(self.bucket_name, object_key)

            # 确保目标目录存在
            Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            async with aiofiles.open(dest_path, 'wb') as f:
                async for chunk in response.stream(8192):
                    await f.write(chunk)

            logger.info(f"文件下载成功: {object_key} -> {dest_path}")

        except S3Error as e:
            logger.error(f"下载文件失败: {e}")
            raise StorageError(f"下载文件失败: {str(e)}")

    async def delete_file(self, object_key: str) -> bool:
        """
        删除文件

        Args:
            object_key: 对象键

        Returns:
            是否删除成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_key)
            logger.info(f"文件删除成功: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"删除文件失败: {e}")
            return False

    async def copy_file(
        self,
        source_object_key: str,
        dest_object_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        复制文件

        Args:
            source_object_key: 源对象键
            dest_object_key: 目标对象键
            metadata: 新的元数据

        Returns:
            是否复制成功
        """
        try:
            result = self.client.copy_object(
                bucket_name=self.bucket_name,
                object_name=dest_object_key,
                source=f"{self.bucket_name}/{source_object_key}",
                metadata=metadata,
            )
            logger.info(f"文件复制成功: {source_object_key} -> {dest_object_key}")
            return True
        except S3Error as e:
            logger.error(f"复制文件失败: {e}")
            return False

    async def list_files(
        self,
        prefix: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出文件

        Args:
            prefix: 前缀
            limit: 限制数量

        Returns:
            文件列表
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )

            files = []
            for i, obj in enumerate(objects):
                if i >= limit:
                    break

                if obj.object_name.endswith('/'):
                    continue  # 跳过目录

                files.append({
                    "object_key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag,
                    "content_type": obj.content_type,
                    "url": self.get_presigned_url(obj.object_name),
                })

            return files

        except S3Error as e:
            logger.error(f"列出文件失败: {e}")
            raise StorageError(f"列出文件失败: {str(e)}")

    async def get_file_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            object_key: 对象键

        Returns:
            文件信息
        """
        try:
            stat = self.client.stat_object(self.bucket_name, object_key)
            return {
                "object_key": object_key,
                "size": stat.size,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
                "url": self.get_presigned_url(object_key),
            }
        except S3Error as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    async def file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_key: 对象键

        Returns:
            文件是否存在
        """
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except S3Error:
            return False


# 全局存储客户端实例
storage_client = MinIOStorage()


async def get_storage_client() -> MinIOStorage:
    """获取存储客户端实例"""
    await storage_client.ensure_bucket_exists()
    return storage_client


__all__ = [
    "MinIOStorage",
    "StorageError",
    "storage_client",
    "get_storage_client",
]