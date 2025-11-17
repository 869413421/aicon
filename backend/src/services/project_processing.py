"""
项目文件处理服务 - 协调文本解析和数据保存

提供服务：
- 文件内容解析处理流程
- 章节段落句子数据保存
- 项目状态和进度跟踪
- 数据清理和统计更新
- 文件内容获取和错误处理
- 失败项目重试机制
- 系统健康检查

设计原则：
- 使用SessionManagedService独立管理会话
- 协调多个服务完成复杂业务流程
- 提供完整的处理状态跟踪
- 异常处理和回滚机制
- 统一的文件处理接口
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.database import get_async_db
from src.core.exceptions import NotFoundError
from src.core.logging import get_logger
from src.models.chapter import Chapter
from src.models.paragraph import Paragraph
from src.models.project import Project, ProjectStatus
from src.models.sentence import Sentence
from src.services.base import SessionManagedService
from src.utils.encoding_detector import decode_file_content
from src.utils.file_handlers import get_file_handler
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class ProjectProcessingService(SessionManagedService):
    """
    项目文件处理服务 - 统一的项目处理接口

    核心功能：
    1. 文件处理流程管理 - 从文件获取到数据存储的完整流程
    2. 文本解析协调 - 集成多种文本解析策略
    3. 状态跟踪管理 - 实时进度更新和错误处理
    4. 数据持久化 - 批量操作和事务管理
    5. 系统健康检查 - 多组件状态监控

    设计特点：
    - 会话自管理：使用 SessionManagedService 独立管理数据库会话
    - 异步优先：所有操作都是异步的，支持高并发
    - 容错设计：完善的错误处理和恢复机制
    - 可观测性：详细的日志记录和状态跟踪
    - 可扩展性：模块化设计便于功能扩展
    """

    def __init__(self):
        super().__init__()
        self._text_parser_service = None
        self._storage_client = None
        # 延迟导入避免循环依赖和初始化开销

    async def _get_text_parser_service(self):
        """延迟导入text_parser_service"""
        if self._text_parser_service is None:
            from src.services.text_parser import text_parser_service
            self._text_parser_service = text_parser_service
        return self._text_parser_service

    async def _get_storage_client(self):
        """延迟导入storage_client"""
        if self._storage_client is None:
            self._storage_client = await get_storage_client()
        return self._storage_client

    async def process_uploaded_file(self, project_id: str, file_content: str) -> Dict:
        """
        处理上传的文件 - 完整的文本解析和数据保存流程

        这是一个完整的文件处理工作流，包含数据清理、文本解析、
        数据保存和状态更新等步骤。整个操作在事务中执行，失败时自动回滚。

        Args:
            project_id: 项目ID，必须是有效的UUID
            file_content: 文件的文本内容，编码应为UTF-8

        Returns:
            Dict[str, Any]: 处理结果，包含：
                - success: 处理是否成功
                - project_id: 项目ID
                - chapters_count: 章节数量
                - paragraphs_count: 段落数量
                - sentences_count: 句子数量
                - message: 处理结果消息

        Raises:
            NotFoundError: 当项目不存在时
            ValidationError: 当文件内容无效时
            BusinessLogicError: 当项目状态不允许处理时
            DatabaseError: 当数据库操作失败时
        """
        try:
            # 1. 获取项目信息
            project = await self._get_project(project_id)

            # 2. 清理已有的数据（避免重复处理）
            await self._clean_existing_data(project_id)

            # 3. 更新项目状态为处理中（10%进度）
            await self._update_project_status(project, ProjectStatus.PARSING, 10)

            # 4. 解析文本内容
            logger.info(f"开始解析项目 {project_id} 的文本内容，长度: {len(file_content)} 字符")
            chapters_data, paragraphs_data, sentences_data = await self._parse_text_content(
                project_id, file_content
            )

            # 5. 更新进度到30%（解析完成）
            await self._update_project_status(project, ProjectStatus.PARSING, 30)

            # 6. 批量保存到数据库
            await self._save_parsed_content(
                project_id, chapters_data, paragraphs_data, sentences_data
            )

            # 7. 更新项目统计信息
            await self._update_project_statistics(project)

            # 8. 标记项目为已解析（100%完成）
            await self._update_project_status(project, ProjectStatus.PARSED, 100)

            # 提交所有更改
            await self.commit()

            logger.info(f"项目 {project_id} 文件处理完成")

            return {
                'success': True,
                'project_id': project_id,
                'chapters_count': len(chapters_data),
                'paragraphs_count': len(paragraphs_data),
                'sentences_count': len(sentences_data),
                'message': '文件处理完成'
            }

        except Exception as e:
            # 发生错误时回滚事务
            await self.rollback()
            logger.error(f"处理项目 {project_id} 文件失败: {e}")
            raise  # 重新抛出异常，由上层处理

    async def _get_project(self, project_id: str) -> Project:
        """
        获取项目信息

        Args:
            project_id: 项目ID

        Returns:
            Project: 项目对象

        Raises:
            NotFoundError: 当项目不存在时
        """
        project = await self.get(Project, project_id)
        if not project:
            raise NotFoundError("项目不存在", resource_type="project", resource_id=project_id)
        return project

    async def _clean_existing_data(self, project_id: str) -> None:
        """
        清理项目已有的数据，避免重复处理

        删除项目相关的所有章节、段落、句子数据，并重置项目统计信息。
        这个操作通常在重新解析文件之前执行。

        Args:
            project_id: 项目ID
        """
        logger.info(f"开始清理项目 {project_id} 的已有数据")

        # 1. 删除句子数据
        deleted_sentences = await Sentence.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_sentences} 个句子")

        # 2. 删除段落数据
        deleted_paragraphs = await Paragraph.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_paragraphs} 个段落")

        # 3. 删除章节数据
        deleted_chapters = await Chapter.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_chapters} 个章节")

        # 4. 重置项目统计信息
        project = await self.get(Project, project_id)
        if project:
            project.chapter_count = 0
            project.paragraph_count = 0
            project.sentence_count = 0
            project.word_count = 0
            project.processing_progress = 0
            project.error_message = None
            project.completed_at = None
            await self.flush()

        logger.info(f"项目 {project_id} 数据清理完成")

    async def _update_project_status(self, project: Project, status: ProjectStatus,
                                     progress: int, error_message: Optional[str] = None) -> None:
        """
        更新项目状态和进度

        更新项目的处理状态、进度百分比，可选择设置错误信息。
        完成时自动设置完成时间。

        Args:
            project: 项目对象
            status: 新的项目状态
            progress: 进度百分比（0-100）
            error_message: 可选的错误信息
        """
        project.status = status.value
        project.processing_progress = progress
        if error_message:
            project.error_message = error_message
        elif status == ProjectStatus.PARSED:
            project.error_message = None
            project.completed_at = datetime.utcnow()

        await self.flush()
        logger.debug(f"更新项目状态: ID={project.id}, 状态={status.value}, 进度={progress}%")

    async def _parse_text_content(self, project_id: str, file_content: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        解析文本内容

        Args:
            project_id: 项目ID
            file_content: 文件内容

        Returns:
            (chapters_data, paragraphs_data, sentences_data)
        """
        text_parser_service = await self._get_text_parser_service()

        # 根据项目设置解析选项
        parse_options = {
            'min_chapter_length': 1000,  # 最小章节长度
        }

        return await text_parser_service.parse_to_models(project_id, file_content, parse_options)

    async def _save_parsed_content(self, project_id: str, chapters_data: List[Dict],
                                   paragraphs_data: List[Dict], sentences_data: List[Dict]) -> None:
        """
        保存解析的内容到数据库

        将文本解析的结果保存到数据库，包含章节、段落、句子三层结构。
        使用批量操作提高性能，并维护数据间的关联关系。

        Args:
            project_id: 项目ID
            chapters_data: 章节数据列表
            paragraphs_data: 段落数据列表
            sentences_data: 句子数据列表
        """
        logger.info(f"开始保存解析内容: {len(chapters_data)} 章节, {len(paragraphs_data)} 段落, {len(sentences_data)} 句子")

        # 1. 批量保存章节
        chapter_ids = await Chapter.batch_create(self.db_session, chapters_data)
        logger.info(f"成功保存 {len(chapter_ids)} 个章节")

        # 2. 更新段落数据中的chapter_id，并批量保存段落
        current_para_index = 0
        para_chapter_mapping = []

        for chapter_idx, chapter_data in enumerate(chapters_data):
            # 计算当前章节的段落数量
            chapter_paragraph_count = chapter_data['paragraph_count']
            if current_para_index + chapter_paragraph_count > len(paragraphs_data):
                # 数据不一致，使用实际可用的数量
                chapter_paragraph_count = len(paragraphs_data) - current_para_index

            # 更新段落的chapter_id
            for i in range(chapter_paragraph_count):
                para_index = current_para_index + i
                if para_index < len(paragraphs_data):
                    paragraphs_data[para_index]['chapter_id'] = chapter_ids[chapter_idx]
                    para_chapter_mapping.append(chapter_ids[chapter_idx])

            current_para_index += chapter_paragraph_count

        # 批量保存段落
        paragraph_ids = await Paragraph.batch_create(self.db_session, paragraphs_data[:current_para_index], para_chapter_mapping)
        logger.info(f"成功保存 {len(paragraph_ids)} 个段落")

        # 3. 更新句子数据中的paragraph_id，并批量保存句子
        current_sent_index = 0
        sent_para_mapping = []

        for para_idx, paragraph_data in enumerate(paragraphs_data[:current_para_index]):
            # 计算当前段落的句子数量
            para_sentence_count = paragraph_data.get('sentence_count', 0)
            if current_sent_index + para_sentence_count > len(sentences_data):
                # 数据不一致，使用实际可用的数量
                para_sentence_count = len(sentences_data) - current_sent_index

            # 更新句子的paragraph_id
            for i in range(para_sentence_count):
                sent_index = current_sent_index + i
                if sent_index < len(sentences_data):
                    sentences_data[sent_index]['paragraph_id'] = paragraph_ids[para_idx]
                    sent_para_mapping.append(paragraph_ids[para_idx])

            current_sent_index += para_sentence_count

        # 批量保存句子
        sentence_ids = await Sentence.batch_create(self.db_session, sentences_data[:current_sent_index], sent_para_mapping)
        logger.info(f"成功保存 {len(sentence_ids)} 个句子")

    async def _update_project_statistics(self, project: Project) -> None:
        """
        更新项目统计信息

        重新计算并更新项目的各项统计数据，包括章节数、段落数、
        句子数和总字数。这些数据用于显示和统计分析。

        Args:
            project: 项目对象
        """
        # 统计章节数量
        chapter_count = await Chapter.count_by_project_id(self.db_session, project.id)
        project.chapter_count = chapter_count

        # 统计段落数量
        paragraphs = await Paragraph.get_by_project_id(self.db_session, project.id)
        project.paragraph_count = len(paragraphs)

        # 统计句子数量
        sentences = await Sentence.get_by_project_id(self.db_session, project.id)
        project.sentence_count = len(sentences)

        # 统计总字数
        total_word_count = 0
        for paragraph in paragraphs:
            total_word_count += paragraph.word_count or 0
        project.word_count = total_word_count

        await self.flush()
        logger.info(f"项目 {project.id} 统计信息更新完成: {chapter_count}章节, {len(paragraphs)}段落, {len(sentences)}句子, {total_word_count}字")

    async def get_file_content(self, project_id: str) -> str:
        """
        获取项目文件内容

        从存储中下载文件并提取文本内容，支持多种文件格式。
        使用临时文件处理大型文件，确保内存安全。

        Args:
            project_id: 项目ID

        Returns:
            str: 文件的文本内容

        Raises:
            NotFoundError: 当项目不存在或文件路径无效时
            ValueError: 当文件无法读取或解码时
        """
        # 使用外部数据库会话获取项目信息
        async with get_async_db() as db:
            project = await db.get(Project, project_id)
            if not project or not project.file_path:
                raise ValueError(f"项目或文件路径无效: {project_id}")

            # 从存储下载文件
            storage = await self._get_storage_client()
            data = await storage.download_file(project.file_path)

            file_type = project.file_type
            handler = get_file_handler(file_type)

            # 创建临时文件处理
            suffix = Path(project.file_path).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fp:
                fp.write(data)
                temp_path = fp.name

            try:
                # 尝试使用文件处理器读取
                content = await handler.read_file(temp_path)
                logger.info(f"成功读取文件 {project.file_path}，内容长度: {len(content)}")
                return content
            except Exception as e:
                # 如果文件处理器失败，尝试直接解码
                logger.warning(f"文件处理器读取失败，尝试直接解码: {e}")
                try:
                    content = decode_file_content(data, project.file_path)
                    logger.info(f"成功解码文件 {project.file_path}，内容长度: {len(content)}")
                    return content
                except Exception as decode_error:
                    logger.error(f"无法解码文件 {project.file_path}: {decode_error}")
                    raise ValueError(f"无法解码文件: {project.file_path}")
            finally:
                # 清理临时文件
                try:
                    import os
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")

    async def mark_failed_safely(self, project_id: str, owner_id: str, message: str) -> None:
        """
        安全地标记项目为失败状态

        当主要处理流程失败时，使用此方法安全地更新项目状态。
        即使在异常情况下也能确保状态更新，避免项目处于不一致状态。

        Args:
            project_id: 项目ID
            owner_id: 项目所有者ID
            message: 失败消息
        """
        from src.services.project import ProjectService

        try:
            # 使用外部数据库会话更新项目状态
            async with get_async_db() as db:
                service = ProjectService(db)
                await service.mark_processing_failed(project_id, owner_id, message)
                logger.info(f"项目 {project_id} 已标记为失败状态: {message}")
        except Exception as e:
            logger.error(f"更新项目失败状态时出错: {e}")
            # 即使状态更新失败，也记录错误，但不抛出异常
            # 这样可以避免掩盖原始的处理错误

    async def process_file_task(self, project_id: str, owner_id: str) -> Dict[str, Any]:
        """
        完整的文件处理任务流程

        该方法封装了文件处理的完整业务逻辑，包括：
        - 项目验证
        - 文件内容获取
        - 文件处理
        - 错误处理和状态管理

        专门为 Celery 任务调用设计，提供完整的异常处理和状态管理。

        Args:
            project_id: 项目ID
            owner_id: 项目所有者ID

        Returns:
            Dict[str, Any]: 处理结果，包含：
                - success: 处理是否成功
                - project_id: 项目ID
                - chapters_count: 章节数量
                - paragraphs_count: 段落数量
                - sentences_count: 句子数量
                - message: 处理结果消息
                - error: 错误信息（如果失败）

        Raises:
            Exception: 当处理失败时抛出异常，调用方应处理异常
        """
        try:
            logger.info(f"开始文件处理任务流程: project_id={project_id}, owner_id={owner_id}")

            # 1. 获取文件内容
            content = await self.get_file_content(project_id)

            # 2. 处理文件内容
            async with self:
                result = await self.process_uploaded_file(
                    project_id=project_id,
                    file_content=content
                )

            # 3. 验证处理结果
            if not result.get("success", True):
                error_msg = result.get("error", "文件处理失败")
                raise Exception(error_msg)

            logger.info(f"文件处理任务流程成功完成: project_id={project_id}")
            return result

        except Exception as e:
            # 统一错误处理
            error_message = f"文件处理失败: {e}"
            logger.error(f"文件处理任务流程失败: project_id={project_id}, error={e}", exc_info=True)

            # 尝试安全标记失败状态
            await self.mark_failed_safely(project_id, owner_id, error_message)
            raise

    async def get_processing_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目处理状态详情

        查询项目的处理进度和详细信息，用于状态轮询和进度显示。
        包含处理统计数据和错误信息。

        Args:
            project_id: 项目ID

        Returns:
            Dict[str, Any] | None: 处理状态详情，包含：
                - success: 处理是否成功
                - chapters_count: 章节数量
                - paragraphs_count: 段落数量
                - sentences_count: 句子数量
                - message: 状态描述
                - error_message: 错误信息（如果有）
                - progress: 处理进度百分比

        Raises:
            NotFoundError: 当项目不存在时
        """
        try:
            # 使用外部数据库会话查询项目信息
            async with get_async_db() as db:
                project = await db.get(Project, project_id)
                if not project:
                    raise NotFoundError("项目不存在", resource_type="project", resource_id=project_id)

                # 根据项目状态构建响应
                response = {
                    "success": True,
                    "chapters_count": project.chapter_count or 0,
                    "paragraphs_count": project.paragraph_count or 0,
                    "sentences_count": project.sentence_count or 0,
                    "word_count": project.word_count or 0,
                    "status": project.status,
                    "progress": project.processing_progress or 0,
                    "message": self._get_status_message(project.status),
                    "error_message": project.error_message,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                    "completed_at": project.completed_at.isoformat() if project.completed_at else None,
                }

                logger.debug(f"项目 {project_id} 状态查询: {project.status} ({response['progress']}%)")
                return response

        except Exception as e:
            logger.error(f"获取项目 {project_id} 处理状态失败: {e}")
            # 发生错误时返回基本信息而不是抛出异常
            return {
                "success": False,
                "chapters_count": 0,
                "paragraphs_count": 0,
                "sentences_count": 0,
                "word_count": 0,
                "status": "unknown",
                "progress": 0,
                "message": "状态查询失败",
                "error_message": str(e),
                "created_at": None,
                "updated_at": None,
                "completed_at": None,
            }

    def _get_status_message(self, status: str) -> str:
        """
        获取状态对应的描述消息

        Args:
            status: 项目状态

        Returns:
            str: 状态描述消息
        """
        status_messages = {
            "uploaded": "文件已上传，等待处理",
            "parsing": "正在解析文件内容",
            "parsed": "文件解析完成",
            "generating": "正在生成内容",
            "completed": "项目已完成",
            "failed": "处理失败",
            "archived": "项目已归档"
        }
        return status_messages.get(status, f"未知状态: {status}")

    async def retry_failed_project(self, project_id: str, owner_id: str) -> Dict[str, Any]:
        """
        重试失败的项目处理

        将失败状态的项目重置为上传状态，并重新启动处理流程。
        只有处于失败状态的项目才能重试。

        Args:
            project_id: 项目ID
            owner_id: 项目所有者ID

        Returns:
            Dict[str, Any]: 重试结果，包含：
                - success: 重试是否成功
                - message: 结果消息
                - processing_result: 处理结果（如果重试成功）

        Raises:
            ValueError: 当项目不存在或状态不允许重试时
        """
        from src.services.project import ProjectService

        # 验证项目状态并重置
        async with get_async_db() as db:
            service = ProjectService(db)
            project = await service.get_project_by_id(project_id, owner_id)

            if not project:
                raise ValueError(f"项目不存在: {project_id}")

            if project.status != "failed":
                return {
                    "success": False,
                    "message": f"项目不是失败状态: {project.status}"
                }

            # 重置项目状态
            project.status = "uploaded"
            project.error_message = None
            project.processing_progress = 0
            await db.commit()

            logger.info(f"项目 {project_id} 状态已重置，开始重新处理")

        # 获取文件内容并重新处理
        try:
            content = await self.get_file_content(project_id)
            # 使用当前服务实例处理文件
            async with self:
                result = await self.process_uploaded_file(
                    project_id=project_id,
                    file_content=content
                )

            return {
                "success": True,
                "message": "重试成功",
                "processing_result": result
            }
        except Exception as e:
            # 如果重试失败，标记为失败状态
            await self.mark_failed_safely(project_id, owner_id, f"重试失败: {e}")
            logger.error(f"重试项目 {project_id} 失败: {e}")
            raise


# 全局实例
project_processing_service = ProjectProcessingService()

__all__ = [
    'ProjectProcessingService',
    'project_processing_service',
]

if __name__ == "__main__":
    import asyncio


    async def main():
        service = ProjectProcessingService()
        # 在这里可以调用服务方法进行测试
        project_id = "c8f5fccd-84ce-45ea-b3d4-b42e48bbdfe7"
        owner_id = "6c11cb2b-d499-4f81-8196-3ea078e9f66a"
        print("Processing file task...")
        res = await service.process_file_task(project_id, owner_id)
        print(res)


    asyncio.run(main())
