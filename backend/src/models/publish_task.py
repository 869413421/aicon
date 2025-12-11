"""
发布任务数据模型
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    pass


class PublishStatus(str, Enum):
    """发布状态枚举"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"


class PublishPlatform(str, Enum):
    """发布平台枚举"""
    BILIBILI = "bilibili"
    YOUTUBE = "youtube"
    DOUYIN = "douyin"


class PublishTask(BaseModel):
    """发布任务模型"""
    __tablename__ = 'publish_tasks'

    # 关联字段
    chapter_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False, index=True, comment="章节外键")
    user_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False, index=True, comment="用户ID")
    platform = Column(String(20), default=PublishPlatform.BILIBILI.value, comment="发布平台")

    # 发布配置
    title = Column(String(200), nullable=False, comment="视频标题")
    desc = Column(Text, comment="视频简介")
    cover_url = Column(String(500), comment="封面URL")
    tid = Column(Integer, default=171, comment="B站分区ID")
    tag = Column(String(500), comment="标签,逗号分隔")
    copyright = Column(Integer, default=1, comment="1原创 2转载")
    source = Column(String(200), comment="转载来源")
    dynamic = Column(String(500), comment="空间动态")
    dtime = Column(Integer, comment="延时发布时间戳")

    # 上传配置
    upload_line = Column(String(20), default='kodo', comment="上传线路")
    upload_limit = Column(Integer, default=3, comment="并发数")

    # 状态字段
    status = Column(String(20), default=PublishStatus.PENDING.value, index=True, comment="发布状态")
    bvid = Column(String(50), comment="B站BV号")
    aid = Column(String(50), comment="B站AV号")
    error_message = Column(Text, comment="错误信息")
    progress = Column(Integer, default=0, comment="上传进度 0-100")
    
    # 任务ID
    celery_task_id = Column(String(100), comment="Celery任务ID")
    
    # 时间字段
    published_at = Column(DateTime, comment="发布完成时间")

    # 关系定义
    chapter = relationship("Chapter", back_populates="publish_tasks")

    # 索引定义
    __table_args__ = (
        Index('idx_publish_task_chapter', 'chapter_id'),
        Index('idx_publish_task_user', 'user_id'),
        Index('idx_publish_task_status', 'status'),
        Index('idx_publish_task_platform', 'platform'),
    )

    def __repr__(self) -> str:
        return f"<PublishTask(id={self.id}, title='{self.title[:30]}...', status={self.status})>"

    def mark_as_uploading(self) -> None:
        """标记为上传中"""
        self.status = PublishStatus.UPLOADING.value

    def mark_as_published(self, bvid: str, aid: str = None) -> None:
        """标记为已发布"""
        self.status = PublishStatus.PUBLISHED.value
        self.bvid = bvid
        self.aid = aid
        self.progress = 100
        self.published_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """标记为失败"""
        self.status = PublishStatus.FAILED.value
        self.error_message = error_message

    def update_progress(self, progress: int) -> None:
        """更新进度"""
        self.progress = max(0, min(100, progress))


class BilibiliAccount(BaseModel):
    """B站账号管理模型"""
    __tablename__ = 'bilibili_accounts'

    user_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True, comment="用户外键")
    account_name = Column(String(100), nullable=False, comment="账号名称")
    cookie_path = Column(String(500), comment="cookie.json存储路径")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login_at = Column(DateTime, comment="最后登录时间")

    # 关系定义
    user = relationship("User")

    # 索引定义
    __table_args__ = (
        Index('idx_bilibili_account_user', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<BilibiliAccount(id={self.id}, account_name='{self.account_name}')>"


__all__ = [
    "PublishTask",
    "PublishStatus",
    "PublishPlatform",
    "BilibiliAccount",
]
