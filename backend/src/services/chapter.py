"""
章节管理服务 - 简洁实现，严格按照data-model.md规范

提供服务：
- 章节的创建、查询、更新、删除
- 章节状态管理
- 章节统计信息
- 章节确认和编辑

设计原则：
- 使用BaseService统一管理数据库会话
- 异常处理遵循统一策略
- 方法职责单一，保持简洁
"""

from typing import List, Optional, Tuple

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessLogicError, NotFoundError
from src.core.logging import get_logger
from src.models.chapter import Chapter, ChapterStatus as ModelChapterStatus
from src.models.paragraph import Paragraph
from src.models.project import Project
from src.models.sentence import Sentence
from src.services.base import BaseService
from src.services.chapter_content_parser import chapter_content_parser

logger = get_logger(__name__)


class ChapterService(BaseService):
    """
    章节管理服务

    负责章节的完整生命周期管理，包括创建、查询、更新、删除和状态管理。
    所有数据库操作都通过基类提供的会话管理功能进行。
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化章节管理服务

        Args:
            db_session: 可选的数据库会话。在FastAPI中通常通过依赖注入提供，
                       在后台任务中可以不提供，让服务自己管理会话
        """
        super().__init__(db_session)
        logger.debug(f"ChapterService 初始化完成，会话管理: {'外部注入' if db_session else '自管理'}")

    async def create_chapter(
            self,
            project_id: str,
            title: str,
            content: str,
            chapter_number: int
    ) -> Chapter:
        """
        创建新章节

        创建一个新章节并初始化基本信息。操作会自动包含在事务中，失败时回滚。

        Args:
            project_id: 项目ID
            title: 章节标题，必填，最大500字符
            content: 章节内容，必填
            chapter_number: 章节序号，从1开始

        Returns:
            Chapter: 创建成功的章节对象，包含生成的ID和创建时间

        Raises:
            ValidationError: 当参数验证失败时
            DatabaseError: 当数据库操作失败时
            NotFoundError: 当项目不存在时
        """
        try:
            # 验证项目是否存在
            project = await self.get(Project, project_id)
            if not project:
                raise NotFoundError(
                    "项目不存在",
                    resource_type="project",
                    resource_id=project_id
                )

            # 检查章节序号是否已存在
            existing_chapter = await self.get_chapter_by_number(project_id, chapter_number)
            if existing_chapter:
                raise BusinessLogicError(
                    f"章节序号 {chapter_number} 已存在",
                    business_rule="chapter_number_unique",
                    context={"project_id": project_id, "chapter_number": chapter_number}
                )

            # 使用内容解析服务重新计算统计信息并生成段落句子结构
            stats, paragraphs_data, sentences_data = await chapter_content_parser.parse_content_with_structure(
                chapter_id=None,  # 临时ID，创建章节后会更新
                content=content
            )
            word_count = stats["word_count"]
            paragraph_count = stats["paragraph_count"]
            sentence_count = stats["sentence_count"]

            # 创建章节对象
            chapter = Chapter(
                project_id=project_id,
                title=title,
                content=content,
                chapter_number=chapter_number,
                word_count=word_count,
                paragraph_count=paragraph_count,
                sentence_count=sentence_count,
                status=ModelChapterStatus.PENDING
            )

            await self.add(chapter)
            await self.flush()  # 获取数据库生成的ID

            # 更新段落数据中的章节ID并创建段落
            if paragraphs_data:
                for paragraph_data in paragraphs_data:
                    paragraph_data["chapter_id"] = chapter.id

                # 批量创建段落
                paragraph_ids = await Paragraph.batch_create(self.db_session, paragraphs_data, [chapter.id] * len(paragraphs_data))

                # 创建句子并关联段落ID
                if sentences_data and paragraph_ids:
                    # 直接使用解析服务已经分配好的句子数据
                    sentence_idx = 0
                    for para_idx, paragraph_id in enumerate(paragraph_ids):
                        if para_idx >= len(paragraphs_data):
                            break

                        # 获取当前段落的句子数量
                        para_sentence_count = paragraphs_data[para_idx]["sentence_count"]

                        # 获取对应的句子数据
                        para_sentences_data = sentences_data[sentence_idx:sentence_idx + para_sentence_count]

                        # 设置句子的段落ID
                        for sentence_data in para_sentences_data:
                            sentence_data["paragraph_id"] = paragraph_id

                        # 批量创建当前段落的句子
                        if para_sentences_data:
                            await Sentence.batch_create(self.db_session, para_sentences_data, [paragraph_id] * len(para_sentences_data))

                        sentence_idx += para_sentence_count

            # 提交事务
            await self.commit()
            await self.refresh(chapter)  # 确保获取最新数据

            logger.info(f"创建章节成功: ID={chapter.id}, 标题={title}, 项目={project_id}")
            return chapter

        except Exception:
            await self.rollback()
            raise  # 重新抛出异常，由中间件处理

    async def get_chapter_by_id(
            self,
            chapter_id: str,
            project_id: Optional[str] = None
    ) -> Chapter:
        """
        根据ID获取章节

        查询指定ID的章节，可选择进行项目权限验证。

        Args:
            chapter_id: 章节ID，必须是有效的UUID格式
            project_id: 项目ID，可选。如果提供，将验证章节是否属于该项目

        Returns:
            Chapter: 查询到的章节对象

        Raises:
            NotFoundError: 当章节不存在或无权限访问时
            ValidationError: 当chapter_id格式无效时
        """
        query = select(Chapter).filter(Chapter.id == chapter_id)
        if project_id:
            query = query.filter(Chapter.project_id == project_id)

        result = await self.execute(query)
        chapter = result.scalar_one_or_none()

        if not chapter:
            error_message = f"章节不存在或无权限访问" if project_id else "章节不存在"
            raise NotFoundError(
                error_message,
                resource_type="chapter",
                resource_id=chapter_id
            )

        logger.debug(f"获取章节成功: ID={chapter_id}, 标题={chapter.title}")
        return chapter

    async def get_chapter_by_number(
            self,
            project_id: str,
            chapter_number: int
    ) -> Optional[Chapter]:
        """
        根据项目ID和章节序号获取章节

        Args:
            project_id: 项目ID
            chapter_number: 章节序号

        Returns:
            Chapter: 查询到的章节对象，如果不存在则返回None
        """
        query = select(Chapter).filter(
            Chapter.project_id == project_id,
            Chapter.chapter_number == chapter_number
        )

        result = await self.execute(query)
        return result.scalar_one_or_none()

    async def get_project_chapters(
            self,
            project_id: str,
            page: int = 1,
            size: int = 20,
            status: Optional[ModelChapterStatus] = None,
            search: Optional[str] = None,
            sort_by: str = "chapter_number",
            sort_order: str = "asc"
    ) -> Tuple[List[Chapter], int]:
        """
        获取项目的章节列表（分页）

        支持多种过滤条件、搜索和排序方式，返回分页结果。

        Args:
            project_id: 项目ID，必填
            page: 页码，从1开始，默认1
            size: 每页大小，默认20，最大100
            status: 章节状态过滤，可选
            search: 搜索关键词，支持在标题、内容中搜索
            sort_by: 排序字段，默认chapter_number，支持title、created_at、updated_at等
            sort_order: 排序顺序，默认asc，支持asc/desc

        Returns:
            Tuple[List[Chapter], int]: (章节列表, 总记录数)

        Raises:
            ValidationError: 当分页参数无效时
            DatabaseError: 当数据库查询失败时
        """
        # 参数验证
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = min(max(size, 1), 100)

        # 构建基础查询
        query = select(Chapter).filter(Chapter.project_id == project_id)

        # 状态过滤
        if status:
            query = query.filter(Chapter.status == status.value)

        # 搜索过滤 - 在标题、内容中搜索
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Chapter.title.ilike(search_term),
                    Chapter.content.ilike(search_term)
                )
            )

        # 获取总数的查询（复用过滤条件）
        count_query = select(func.count(Chapter.id)).filter(Chapter.project_id == project_id)
        if status:
            count_query = count_query.filter(Chapter.status == status.value)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.filter(
                or_(
                    Chapter.title.ilike(search_term),
                    Chapter.content.ilike(search_term)
                )
            )

        # 执行总数查询
        total_result = await self.execute(count_query)
        total = total_result.scalar()

        # 排序处理
        if hasattr(Chapter, sort_by):
            sort_column = getattr(Chapter, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
        else:
            # 默认按章节序号升序
            query = query.order_by(Chapter.chapter_number)

        # 分页处理
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 执行主查询
        result = await self.execute(query)
        chapters = result.scalars().all()

        logger.debug(f"查询章节列表: 项目={project_id}, 总数={total}, 当前页={page}, 数量={len(chapters)}")
        return list(chapters), total

    async def update_chapter(
            self,
            chapter_id: str,
            project_id: str,
            **updates
    ) -> Chapter:
        """
        更新章节信息

        Args:
            chapter_id: 章节ID
            project_id: 项目ID
            **updates: 更新字段

        Returns:
            更新后的章节
        """
        chapter = await self.get_chapter_by_id(chapter_id, project_id)

        # 更新字段
        for field, value in updates.items():
            if hasattr(chapter, field) and value is not None:
                setattr(chapter, field, value)

        # 如果更新了内容，使用内容解析服务重新计算统计信息并更新段落句子结构
        if 'content' in updates and updates['content']:
            content = updates['content']
            stats, paragraphs_data, sentences_data = await chapter_content_parser.parse_content_with_structure(
                chapter_id=chapter.id,
                content=content
            )
            chapter.word_count = stats["word_count"]
            chapter.paragraph_count = stats["paragraph_count"]
            chapter.sentence_count = stats["sentence_count"]

            # 删除现有的段落和句子（级联删除）
            await self.execute(
                select(Paragraph).where(Paragraph.chapter_id == chapter.id)
            )
            existing_paragraphs_result = await self.execute(
                select(Paragraph).where(Paragraph.chapter_id == chapter.id)
            )
            existing_paragraphs = existing_paragraphs_result.scalars().all()

            for para in existing_paragraphs:
                await self.delete(para)

            # 创建新的段落和句子
            if paragraphs_data:
                # 批量创建段落
                paragraph_ids = await Paragraph.batch_create(self.db_session, paragraphs_data, [chapter.id] * len(paragraphs_data))

                # 创建句子并关联段落ID
                if sentences_data and paragraph_ids:
                    # 直接使用解析服务已经分配好的句子数据
                    sentence_idx = 0
                    for para_idx, paragraph_id in enumerate(paragraph_ids):
                        if para_idx >= len(paragraphs_data):
                            break

                        # 获取当前段落的句子数量
                        para_sentence_count = paragraphs_data[para_idx]["sentence_count"]

                        # 获取对应的句子数据
                        para_sentences_data = sentences_data[sentence_idx:sentence_idx + para_sentence_count]

                        # 设置句子的段落ID
                        for sentence_data in para_sentences_data:
                            sentence_data["paragraph_id"] = paragraph_id

                        # 批量创建当前段落的句子
                        if para_sentences_data:
                            await Sentence.batch_create(self.db_session, para_sentences_data, [paragraph_id] * len(para_sentences_data))

                        sentence_idx += para_sentence_count

        await self.commit()
        await self.refresh(chapter)

        logger.info(f"更新章节成功: ID={chapter_id}, 更新字段={list(updates.keys())}")
        return chapter

    async def confirm_chapter(
            self,
            chapter_id: str,
            project_id: str
    ) -> Chapter:
        """
        确认章节

        Args:
            chapter_id: 章节ID
            project_id: 项目ID

        Returns:
            确认后的章节
        """
        chapter = await self.get_chapter_by_id(chapter_id, project_id)

        # 检查是否已确认
        if chapter.is_confirmed:
            raise BusinessLogicError(
                "章节已经确认",
                business_rule="chapter_already_confirmed",
                context={"chapter_id": chapter_id, "project_id": project_id}
            )

        # 执行确认操作
        chapter.is_confirmed = True
        chapter.status = ModelChapterStatus.CONFIRMED
        # confirmed_at 字段会在模型的 save 方法中自动更新

        await self.commit()
        await self.refresh(chapter)

        logger.info(f"确认章节成功: ID={chapter_id}, 标题={chapter.title}")
        return chapter

    async def delete_chapter(
            self,
            chapter_id: str,
            project_id: str
    ) -> bool:
        """
        删除章节及其所有相关的段落和句子

        Args:
            chapter_id: 章节ID
            project_id: 项目ID

        Returns:
            是否删除成功
        """
        chapter = await self.get_chapter_by_id(chapter_id, project_id)

        # 检查是否已确认（已确认的章节不能删除）
        if chapter.is_confirmed:
            raise BusinessLogicError(
                "已确认的章节不能删除",
                business_rule="confirmed_chapter_delete",
                context={"chapter_id": chapter_id, "project_id": project_id}
            )

        # 先统计要删除的段落和句子数量（用于日志记录）
        from src.models.paragraph import Paragraph
        from src.models.sentence import Sentence
        from sqlalchemy import func

        # 统计段落数量
        paragraph_count_result = await self.execute(
            select(func.count(Paragraph.id)).where(Paragraph.chapter_id == chapter_id)
        )
        paragraph_count = paragraph_count_result.scalar() or 0

        # 统计句子数量
        sentence_count_result = await self.execute(
            select(func.count(Sentence.id)).where(Sentence.paragraph_id.in_(
                select(Paragraph.id).where(Paragraph.chapter_id == chapter_id)
            ))
        )
        sentence_count = sentence_count_result.scalar() or 0

        logger.info(f"开始删除章节: ID={chapter_id}, 标题={chapter.title}, 将删除 {paragraph_count} 个段落, {sentence_count} 个句子")

        # 删除章节（会级联删除所有段落和句子）
        await self.delete(chapter)
        await self.commit()

        logger.info(f"删除章节成功: ID={chapter_id}, 标题={chapter.title}, 已删除 {paragraph_count} 个段落, {sentence_count} 个句子")
        return True


__all__ = [
    "ChapterService",
]
