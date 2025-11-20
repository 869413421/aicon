"""
段落管理服务 - 负责段落的创建、更新、删除和查询

提供服务：
- 段落的创建、查询、更新、删除
- 段落内容变更时的句子解析
- 段落批量操作

设计原则：
- 使用BaseService统一管理数据库会话
- 复用sentence_splitter进行句子分割
- 参考ChapterService的实现模式
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessLogicError, NotFoundError
from src.core.logging import get_logger
from src.models.chapter import Chapter
from src.models.paragraph import Paragraph, ParagraphAction
from src.models.sentence import Sentence, SentenceStatus
from src.services.base import BaseService
from src.utils.text_utils import sentence_splitter

logger = get_logger(__name__)


class ParagraphService(BaseService):
    """
    段落管理服务

    负责段落的完整生命周期管理，包括创建、查询、更新、删除。
    当段落内容变更时，自动重新解析句子。
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化段落管理服务

        Args:
            db_session: 可选的数据库会话
        """
        super().__init__(db_session)
        logger.debug(f"ParagraphService 初始化完成，会话管理: {'外部注入' if db_session else '自管理'}")

    async def create_paragraph(
            self,
            chapter_id: str,
            content: str,
            order_index: int
    ) -> Paragraph:
        """
        创建新段落并自动解析句子

        Args:
            chapter_id: 章节ID
            content: 段落内容
            order_index: 在章节中的顺序

        Returns:
            Paragraph: 创建成功的段落对象

        Raises:
            NotFoundError: 当章节不存在时
            BusinessLogicError: 当业务逻辑错误时
        """
        try:
            # 验证章节是否存在
            chapter = await self.get(Chapter, chapter_id)
            if not chapter:
                raise NotFoundError(
                    "章节不存在",
                    resource_type="chapter",
                    resource_id=chapter_id
                )

            # 计算段落统计信息
            word_count = len(content.replace(' ', ''))

            # 使用sentence_splitter解析句子
            sentences_list = sentence_splitter.split_text(content)
            sentence_count = len(sentences_list)

            # 创建段落对象
            paragraph = Paragraph(
                chapter_id=chapter_id,
                content=content,
                order_index=order_index,
                word_count=word_count,
                sentence_count=sentence_count,
                action=ParagraphAction.KEEP,
                is_confirmed=False
            )

            await self.add(paragraph)
            await self.flush()  # 获取数据库生成的ID

            # 创建句子数据
            if sentences_list:
                sentences_data = []
                for sent_idx, sentence_text in enumerate(sentences_list):
                    if not sentence_text.strip():
                        continue

                    sentence_data = {
                        "paragraph_id": paragraph.id,
                        "content": sentence_text.strip(),
                        "order_index": sent_idx + 1,
                        "word_count": len(sentence_text.replace(' ', '')),
                        "character_count": len(sentence_text),
                        "status": SentenceStatus.PENDING.value,
                        "retry_count": 0,
                        "is_manual_edited": False,
                    }
                    sentences_data.append(sentence_data)

                # 批量创建句子
                if sentences_data:
                    await Sentence.batch_create(
                        self.db_session,
                        sentences_data,
                        [paragraph.id] * len(sentences_data)
                    )

            # 提交事务
            await self.commit()
            await self.refresh(paragraph)

            logger.info(f"创建段落成功: ID={paragraph.id}, 章节={chapter_id}, 句子数={sentence_count}")
            return paragraph

        except Exception:
            await self.rollback()
            raise

    async def get_paragraph_by_id(
            self,
            paragraph_id: str,
            chapter_id: Optional[str] = None
    ) -> Paragraph:
        """
        根据ID获取段落

        Args:
            paragraph_id: 段落ID
            chapter_id: 章节ID，可选。如果提供，将验证段落是否属于该章节

        Returns:
            Paragraph: 查询到的段落对象

        Raises:
            NotFoundError: 当段落不存在或无权限访问时
        """
        query = select(Paragraph).filter(Paragraph.id == paragraph_id)
        if chapter_id:
            query = query.filter(Paragraph.chapter_id == chapter_id)

        result = await self.execute(query)
        paragraph = result.scalar_one_or_none()

        if not paragraph:
            error_message = f"段落不存在或无权限访问" if chapter_id else "段落不存在"
            raise NotFoundError(
                error_message,
                resource_type="paragraph",
                resource_id=paragraph_id
            )

        logger.debug(f"获取段落成功: ID={paragraph_id}")
        return paragraph

    async def get_chapter_paragraphs(
            self,
            chapter_id: str
    ) -> List[Paragraph]:
        """
        获取章节的所有段落

        Args:
            chapter_id: 章节ID

        Returns:
            List[Paragraph]: 段落列表，按order_index排序
        """
        # 验证章节是否存在
        chapter = await self.get(Chapter, chapter_id)
        if not chapter:
            raise NotFoundError(
                "章节不存在",
                resource_type="chapter",
                resource_id=chapter_id
            )

        query = select(Paragraph).filter(
            Paragraph.chapter_id == chapter_id
        ).order_by(Paragraph.order_index)

        result = await self.execute(query)
        paragraphs = result.scalars().all()

        logger.debug(f"查询章节段落: 章节={chapter_id}, 数量={len(paragraphs)}")
        return list(paragraphs)

    async def update_paragraph(
            self,
            paragraph_id: str,
            chapter_id: str,
            **updates
    ) -> Paragraph:
        """
        更新段落信息，如果内容变更则重新解析句子

        Args:
            paragraph_id: 段落ID
            chapter_id: 章节ID
            **updates: 更新字段

        Returns:
            更新后的段落
        """
        paragraph = await self.get_paragraph_by_id(paragraph_id, chapter_id)

        # 检查内容是否变更
        content_changed = 'content' in updates and updates['content'] != paragraph.content

        # 更新字段
        for field, value in updates.items():
            if hasattr(paragraph, field) and value is not None:
                setattr(paragraph, field, value)

        # 如果内容变更，重新解析句子
        if content_changed:
            new_content = updates['content']

            # 计算新的统计信息
            word_count = len(new_content.replace(' ', ''))
            sentences_list = sentence_splitter.split_text(new_content)
            sentence_count = len(sentences_list)

            # 更新段落统计
            paragraph.word_count = word_count
            paragraph.sentence_count = sentence_count

            # 删除现有句子
            existing_sentences_result = await self.execute(
                select(Sentence).where(Sentence.paragraph_id == paragraph_id)
            )
            existing_sentences = existing_sentences_result.scalars().all()

            for sentence in existing_sentences:
                await self.delete(sentence)

            # 创建新句子
            if sentences_list:
                sentences_data = []
                for sent_idx, sentence_text in enumerate(sentences_list):
                    if not sentence_text.strip():
                        continue

                    sentence_data = {
                        "paragraph_id": paragraph.id,
                        "content": sentence_text.strip(),
                        "order_index": sent_idx + 1,
                        "word_count": len(sentence_text.replace(' ', '')),
                        "character_count": len(sentence_text),
                        "status": SentenceStatus.PENDING.value,
                        "retry_count": 0,
                        "is_manual_edited": False,
                    }
                    sentences_data.append(sentence_data)

                # 批量创建句子
                if sentences_data:
                    await Sentence.batch_create(
                        self.db_session,
                        sentences_data,
                        [paragraph.id] * len(sentences_data)
                    )

            logger.info(f"段落内容变更，重新解析句子: ID={paragraph_id}, 新句子数={sentence_count}")

        await self.commit()
        await self.refresh(paragraph)

        logger.info(f"更新段落成功: ID={paragraph_id}, 更新字段={list(updates.keys())}")
        return paragraph

    async def delete_paragraph(
            self,
            paragraph_id: str,
            chapter_id: str
    ) -> bool:
        """
        删除段落及其所有关联的句子

        Args:
            paragraph_id: 段落ID
            chapter_id: 章节ID

        Returns:
            是否删除成功
        """
        paragraph = await self.get_paragraph_by_id(paragraph_id, chapter_id)

        # 统计要删除的句子数量
        sentence_count_result = await self.execute(
            select(Sentence).where(Sentence.paragraph_id == paragraph_id)
        )
        sentences = sentence_count_result.scalars().all()
        sentence_count = len(sentences)

        logger.info(f"开始删除段落: ID={paragraph_id}, 将删除 {sentence_count} 个句子")

        # 删除段落（会级联删除所有句子）
        await self.delete(paragraph)
        await self.commit()

        logger.info(f"删除段落成功: ID={paragraph_id}, 已删除 {sentence_count} 个句子")
        return True


__all__ = [
    "ParagraphService",
]
