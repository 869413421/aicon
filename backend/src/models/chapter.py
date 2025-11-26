"""
章节模型 - 文档的逻辑分割单元
严格按照data-model.md规范实现
"""

import uuid
from enum import Enum
from typing import Dict, List, TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    pass


class ChapterStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    GENERATING_PROMPTS = "generating_prompts"  # 生成提示词中
    PROMPTS_GENERATED = "prompts_generated"  # 提示词已生成
    GENERATING_VIDEO = "generating_video"  # 生成视频中
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Chapter(BaseModel):
    """章节模型 - 文档的逻辑分割单元"""
    __tablename__ = 'chapters'

    # 基础字段 (ID, created_at, updated_at 继承自 BaseModel)
    project_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True,
                        comment="项目外键")
    title = Column(String(500), nullable=False, comment="章节标题")
    content = Column(Text, nullable=False, comment="章节原始内容")

    # 结构信息
    chapter_number = Column(Integer, nullable=False, comment="章节序号")
    word_count = Column(Integer, default=0, comment="字数统计")
    paragraph_count = Column(Integer, default=0, comment="段落数量")
    sentence_count = Column(Integer, default=0, comment="句子数量")

    # 处理状态
    status = Column(String(20), default=ChapterStatus.PENDING, index=True, comment="处理状态")
    is_confirmed = Column(Boolean, default=False, comment="是否已确认")
    confirmed_at = Column(DateTime, nullable=True, comment="确认时间")

    # 编辑信息
    edited_content = Column(Text, nullable=True, comment="用户编辑后的内容")
    editing_notes = Column(Text, nullable=True, comment="编辑备注")

    # 生成信息
    generation_settings = Column(Text, nullable=True, comment="章节级生成配置")
    video_url = Column(String(500), nullable=True, comment="最终视频URL")
    video_duration = Column(Integer, nullable=True, comment="视频时长（秒）")

    # 关系定义
    project = relationship("Project", back_populates="chapters")
    paragraphs = relationship("Paragraph", back_populates="chapter", cascade="all, delete-orphan")

    # 索引定义
    __table_args__ = (
        Index('idx_chapter_project', 'project_id'),
        Index('idx_chapter_status', 'status'),
        Index('idx_chapter_number', 'chapter_number'),
    )

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, title='{self.title[:50]}...', number={self.chapter_number})>"

    # ==================== 批量操作方法 ====================

    @classmethod
    async def batch_create(cls, db_session, chapters_data: List[Dict]) -> List[str]:
        """
        批量创建章节记录

        Args:
            db_session: 数据库会话
            chapters_data: 章节数据列表，格式:
                [
                    {
                        'project_id': str,
                        'title': str,
                        'content': str,
                        'chapter_number': int,
                        'word_count': int,
                        'paragraph_count': int,
                        'sentence_count': int,
                        'status': str
                    },
                    ...
                ]

        Returns:
            创建的章节ID列表
        """
        if not chapters_data:
            return []

        # 生成ID并添加到数据中
        chapter_ids = []
        for chapter_data in chapters_data:
            chapter_id = uuid.uuid4()
            chapter_data['id'] = chapter_id
            chapter_data.setdefault('is_confirmed', False)
            chapter_ids.append(chapter_id)

        # 批量插入
        await db_session.execute(
            cls.__table__.insert(),
            chapters_data
        )

        # 提交以确保获取ID
        await db_session.flush()

        # 返回插入的ID列表
        return chapter_ids

    @classmethod
    async def batch_update_statistics(cls, db_session, updates: List[Dict]) -> None:
        """
        批量更新章节统计信息

        Args:
            db_session: 数据库会话
            updates: 更新数据列表，格式:
                [
                    {
                        'id': str,
                        'word_count': int,
                        'paragraph_count': int,
                        'sentence_count': int
                    },
                    ...
                ]
        """
        if not updates:
            return

        for update in updates:
            chapter_id = update.pop('id')
            await db_session.execute(
                cls.__table__.update()
                .where(cls.__table__.c.id == chapter_id)
                .values(**update)
            )

    @classmethod
    async def get_by_project_id(cls, db_session, project_id: str) -> List['Chapter']:
        """
        获取项目的所有章节

        Args:
            db_session: 数据库会话
            project_id: 项目ID

        Returns:
            章节列表
        """
        result = await db_session.execute(
            select(cls).where(cls.project_id == project_id)
            .order_by(cls.chapter_number)
        )
        return result.scalars().all()

    @classmethod
    async def count_by_project_id(cls, db_session, project_id: str) -> int:
        """
        统计项目的章节数量

        Args:
            db_session: 数据库会话
            project_id: 项目ID

        Returns:
            章节数量
        """
        from sqlalchemy import func
        result = await db_session.execute(
            select(func.count(cls.id)).where(cls.project_id == project_id)
        )
        return result.scalar()

    @classmethod
    async def delete_by_project_id(cls, db_session, project_id: str) -> int:
        """
        删除项目的所有章节

        Args:
            db_session: 数据库会话
            project_id: 项目ID

        Returns:
            删除的章节数量
        """
        # 先统计数量
        count = await cls.count_by_project_id(db_session, project_id)

        if count > 0:
            # 执行删除（会级联删除段落数据）
            await db_session.execute(
                cls.__table__.delete().where(cls.project_id == project_id)
            )
            await db_session.flush()

        return count


__all__ = [
    "Chapter",
    "ChapterStatus",
]
