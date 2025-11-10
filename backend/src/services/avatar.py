"""
头像上传服务模块
"""

import hashlib
import io
from typing import Optional

from PIL import Image
from minio import Minio
from minio.error import S3Error

from src.core.config import settings
from src.core.exceptions import FileUploadError, ValidationError


class AvatarService:
    """头像上传服务类"""

    def __init__(self):
        """初始化头像服务"""
        self.minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION
        )
        self.bucket_name = settings.AVATAR_BUCKET_NAME

    async def _ensure_bucket_exists(self):
        """确保头像存储桶存在"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(
                    bucket_name=self.bucket_name,
                    location=settings.MINIO_REGION
                )
                # 设置桶策略为公共读取
                policy = f"""
                {{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Effect": "Allow",
                            "Principal": {{
                                "AWS": ["*"]
                            }},
                            "Action": "s3:GetObject",
                            "Resource": ["arn:aws:s3:::{self.bucket_name}/*"]
                        }}
                    ]
                }}
                """
                self.minio_client.set_bucket_policy(self.bucket_name, policy)
        except S3Error as e:
            raise FileUploadError(f"MinIO存储桶操作失败: {str(e)}")

    async def _validate_image(self, file_data: bytes, filename: str) -> str:
        """验证图片文件"""
        # 检查文件大小
        if len(file_data) > settings.MAX_AVATAR_SIZE:
            raise ValidationError(f"图片文件大小不能超过 {settings.MAX_AVATAR_SIZE // (1024 * 1024)}MB")

        # 检查文件扩展名
        file_ext = filename.lower().split('.')[-1]
        if file_ext not in settings.ALLOWED_AVATAR_TYPES:
            raise ValidationError(f"不支持的图片格式，支持的格式: {', '.join(settings.ALLOWED_AVATAR_TYPES)}")

        # 验证图片内容
        try:
            img = Image.open(io.BytesIO(file_data))
            img.verify()  # 验证图片完整性
            # 重新打开图片获取格式信息
            img = Image.open(io.BytesIO(file_data))

            # 检查图片尺寸
            width, height = img.size
            max_size = 2000  # 最大尺寸限制
            if width > max_size or height > max_size:
                raise ValidationError(f"图片尺寸过大，最大允许 {max_size}x{max_size}")

            # 返回实际图片格式
            return img.format.lower()
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError("无效的图片文件")

    async def _resize_image(self, file_data: bytes, format_type: str = "JPEG") -> bytes:
        """调整图片尺寸"""
        try:
            img = Image.open(io.BytesIO(file_data))

            # 如果是PNG格式且需要透明背景，转换为RGBA
            if format_type.lower() == 'png' and img.mode != 'RGBA':
                img = img.convert('RGBA')
            elif img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')

            # 计算新尺寸（保持宽高比）
            width, height = img.size
            target_width, target_height = settings.AVATAR_DEFAULT_SIZE

            # 计算缩放比例
            scale = min(target_width / width, target_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            # 调整尺寸
            if new_width != width or new_height != height:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 创建目标尺寸的背景画布
            background = Image.new('RGB', (target_width, target_height), (255, 255, 255))

            # 计算居中位置
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2

            # 粘贴图片到中心
            if img.mode == 'RGBA':
                background.paste(img, (x_offset, y_offset), img)
            else:
                background.paste(img, (x_offset, y_offset))

            # 保存为字节流
            output = io.BytesIO()
            background.save(output, format=format_type, quality=85, optimize=True)
            output.seek(0)

            return output.getvalue()
        except Exception as e:
            raise ValidationError(f"图片处理失败: {str(e)}")

    def _generate_object_name(self, user_id: int, original_filename: str, format_type: str) -> str:
        """生成对象存储名称"""
        file_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        timestamp = int(__import__('time').time())
        ext = format_type.lower()
        return f"avatars/{user_id}/{file_hash}_{timestamp}.{ext}"

    async def upload_avatar(self, user_id: str, file_data: bytes, filename: str) -> str:
        """上传头像"""
        try:
            # 确保存储桶存在
            await self._ensure_bucket_exists()

            # 验证图片
            format_type = await self._validate_image(file_data, filename)

            # 调整图片尺寸
            processed_data = await self._resize_image(file_data, format_type)

            # 生成对象名称
            object_name = self._generate_object_name(user_id, filename, format_type)

            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(processed_data),
                length=len(processed_data),
                content_type=f"image/{format_type.lower()}"
            )

            # 构建访问URL
            avatar_url = f"{settings.minio_url}/{self.bucket_name}/{object_name}"

            return avatar_url

        except S3Error as e:
            raise FileUploadError(f"文件上传失败: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, FileUploadError)):
                raise
            raise FileUploadError(f"头像上传处理失败: {str(e)}")

    async def delete_avatar(self, avatar_url: str) -> bool:
        """删除头像"""
        try:
            if not avatar_url:
                return False

            # 从URL中提取对象名称
            if f"/{self.bucket_name}/" in avatar_url:
                object_name = avatar_url.split(f"/{self.bucket_name}/", 1)[1]
            else:
                return False

            # 检查对象是否存在
            try:
                self.minio_client.stat_object(self.bucket_name, object_name)
            except S3Error:
                return False  # 对象不存在，认为删除成功

            # 删除对象
            self.minio_client.remove_object(self.bucket_name, object_name)
            return True

        except S3Error as e:
            raise FileUploadError(f"文件删除失败: {str(e)}")
        except Exception as e:
            raise FileUploadError(f"头像删除处理失败: {str(e)}")

    async def get_avatar_info(self, avatar_url: str) -> Optional[dict]:
        """获取头像信息"""
        try:
            if not avatar_url:
                return None

            # 从URL中提取对象名称
            if f"/{self.bucket_name}/" not in avatar_url:
                return None

            object_name = avatar_url.split(f"/{self.bucket_name}/", 1)[1]

            # 获取对象统计信息
            stat = self.minio_client.stat_object(self.bucket_name, object_name)

            return {
                "object_name": object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "etag": stat.etag
            }

        except S3Error:
            return None
        except Exception:
            return None


# 创建头像服务实例
avatar_service = AvatarService()
