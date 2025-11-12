"""
项目数据模型 - 文档管理和项目核心功能
"""

import json
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, ForeignKey, Index, Float
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    DRAFT = "draft"              # 草稿
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    ARCHIVED = "archived"       # 已归档


class FileProcessingStatus(str, Enum):
    """文件处理状态枚举"""
    PENDING = "pending"          # 等待处理
    UPLOADING = "uploading"      # 上传中
    UPLOADED = "uploaded"        # 已上传
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 处理完成
    FAILED = "failed"           # 处理失败


class SupportedFileType(str, Enum):
    """支持的文件类型枚举"""
    TXT = "txt"                 # 纯文本
    MD = "md"                   # Markdown
    DOCX = "docx"               # Word文档
    EPUB = "epub"               # EPUB电子书


class Project(BaseModel):
    """项目模型 - 文档管理和内容处理的核心"""
    __tablename__ = 'projects'

    # 基本信息
    title = Column(String(200), nullable=False, comment="项目标题")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(String(20), default=ProjectStatus.DRAFT.value, nullable=False, comment="项目状态")

    # 用户关系
    user_id = Column(String, ForeignKey('users.id'), nullable=False, comment="所有者用户ID")

    # 文件信息
    original_filename = Column(String(255), nullable=True, comment="原始文件名")
    file_path = Column(String(500), nullable=True, comment="文件存储路径")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    file_type = Column(String(10), nullable=True, comment="文件类型")
    file_hash = Column(String(64), nullable=True, comment="文件哈希值（SHA-256）")
    file_processing_status = Column(String(20), default=FileProcessingStatus.PENDING.value, nullable=False, comment="文件处理状态")

    # 文档元信息
    total_chapters = Column(Integer, default=0, nullable=False, comment="章节数量")
    total_paragraphs = Column(Integer, default=0, nullable=False, comment="段落数量")
    total_sentences = Column(Integer, default=0, nullable=False, comment="句子数量")
    word_count = Column(Integer, default=0, nullable=False, comment="字数统计")

    # 处理配置
    processing_config = Column(JSON, nullable=True, comment="处理配置（JSON格式）")

    # MinIO存储信息
    minio_bucket = Column(String(100), nullable=True, comment="MinIO存储桶")
    minio_object_key = Column(String(500), nullable=True, comment="MinIO对象键")

    # 处理结果和错误
    processing_error = Column(Text, nullable=True, comment="处理错误信息")
    processing_progress = Column(Float, default=0.0, nullable=False, comment="处理进度（0-100）")

    # 状态标志
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")

    # 关系定义
    # chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    # generation_tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_project_user_status', 'user_id', 'status', 'is_deleted'),
        Index('idx_project_file_status', 'file_processing_status', 'created_at'),
        Index('idx_project_title_search', 'title'),
    )

    def get_processing_config(self) -> Dict[str, Any]:
        """获取处理配置"""
        if self.processing_config:
            if isinstance(self.processing_config, dict):
                return self.processing_config
            elif isinstance(self.processing_config, str):
                try:
                    return json.loads(self.processing_config)
                except (json.JSONDecodeError, TypeError):
                    return {}
        return {}

    def set_processing_config(self, config: Dict[str, Any]) -> None:
        """设置处理配置"""
        self.processing_config = config

    def get_file_extension(self) -> Optional[str]:
        """获取文件扩展名"""
        if self.original_filename:
            return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else None
        return None

    def is_supported_file_type(self) -> bool:
        """检查是否为支持的文件类型"""
        if not self.file_type:
            return False
        try:
            return self.file_type in [ft.value for ft in SupportedFileType]
        except ValueError:
            return False

    def get_file_size_mb(self) -> float:
        """获取文件大小（MB）"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0

    def update_processing_progress(self, progress: float) -> None:
        """更新处理进度"""
        self.processing_progress = max(0.0, min(100.0, progress))

    def mark_as_failed(self, error_message: str) -> None:
        """标记为处理失败"""
        self.status = ProjectStatus.FAILED.value
        self.file_processing_status = FileProcessingStatus.FAILED.value
        self.processing_error = error_message
        self.update_processing_progress(0.0)

    def mark_as_completed(self) -> None:
        """标记为处理完成"""
        self.status = ProjectStatus.COMPLETED.value
        self.file_processing_status = FileProcessingStatus.COMPLETED.value
        self.update_processing_progress(100.0)
        self.processing_error = None

    def can_be_processed(self) -> bool:
        """检查是否可以进行处理"""
        return (
            self.status in [ProjectStatus.DRAFT.value, ProjectStatus.FAILED.value] and
            self.file_processing_status in [FileProcessingStatus.UPLOADED.value, FileProcessingStatus.FAILED.value] and
            self.file_path and self.is_supported_file_type()
        )

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """转换为字典，重写基类方法"""
        exclude = exclude or []
        result = super().to_dict(exclude=exclude)

        # 添加计算字段
        result['file_size_mb'] = self.get_file_size_mb()
        result['file_extension'] = self.get_file_extension()
        result['is_supported_file_type'] = self.is_supported_file_type()
        result['can_be_processed'] = self.can_be_processed()

        # 确保枚举值存在
        if 'status' not in result or not result['status']:
            result['status'] = ProjectStatus.DRAFT.value
        if 'file_processing_status' not in result or not result['file_processing_status']:
            result['file_processing_status'] = FileProcessingStatus.PENDING.value

        return result

    @classmethod
    async def get_by_user_id(cls, db_session, user_id: str, include_deleted: bool = False):
        """获取用户的项目列表"""
        from sqlalchemy import select

        query = select(cls).filter(cls.user_id == user_id)
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)

        result = await db_session.execute(query.order_by(cls.created_at.desc()))
        return result.scalars().all()

    @classmethod
    async def get_by_id_and_user(cls, db_session, project_id: str, user_id: str):
        """根据ID和用户获取项目"""
        from sqlalchemy import select

        result = await db_session.execute(
            select(cls).filter(
                cls.id == project_id,
                cls.user_id == user_id,
                cls.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create_project(cls, db_session, user_id: str, title: str,
                           description: str = None, original_filename: str = None):
        """创建新项目"""
        project = cls(
            user_id=user_id,
            title=title,
            description=description,
            original_filename=original_filename,
            status=ProjectStatus.DRAFT.value,
            file_processing_status=FileProcessingStatus.PENDING.value
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project

    def soft_delete(self) -> None:
        """软删除项目"""
        self.is_deleted = True

    def restore(self) -> None:
        """恢复已删除的项目"""
        self.is_deleted = False


__all__ = [
    "Project",
    "ProjectStatus",
    "FileProcessingStatus",
    "SupportedFileType",
]