"""
文件处理Celery任务模块
提供异步文件处理、内容分析、统计计算等功能
"""

import os
import tempfile
import traceback
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from celery import Celery
from celery.exceptions import Retry

from src.core.config import settings
from src.core.logging import get_logger
from src.models.project import (
    Project, ProjectStatus, FileProcessingStatus, SupportedFileType
)
# 延迟导入以避免循环依赖
# from src.services.project_service import ProjectService, ProjectServiceError
# from src.utils.file_handlers import get_file_handler, FileProcessingError
# from src.utils.storage import get_storage_client, StorageError

logger = get_logger(__name__)

# 创建Celery实例
celery_app = Celery(
    'file_processing',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['src.tasks.file_processing']
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=getattr(settings, 'CELERY_TASK_TIME_LIMIT', 300),
    task_soft_time_limit=getattr(settings, 'CELERY_TASK_SOFT_TIME_LIMIT', 240),
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由配置
celery_app.conf.task_routes = {
    'src.tasks.file_processing.process_uploaded_file': {'queue': 'file_processing'},
    'src.tasks.file_processing.analyze_file_content': {'queue': 'content_analysis'},
    'src.tasks.file_processing.extract_metadata': {'queue': 'metadata_extraction'},
    'src.tasks.file_processing.cleanup_temp_files': {'queue': 'cleanup'},
}

# 任务优先级配置
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_direct = True


def run_async_task(coro):
    """在同步上下文中运行异步任务"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name='process_uploaded_file')
def process_uploaded_file(self, project_id: str, user_id: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    处理上传的文件

    Args:
        project_id: 项目ID
        user_id: 用户ID
        file_path: 文件路径（可选，如果未提供则从存储下载）

    Returns:
        处理结果字典
    """
    task_id = self.request.id
    logger.info(f"开始处理文件任务: {task_id}, 项目ID: {project_id}")

    async def _process_file():
        from src.core.database import get_async_session
        from src.services.project import ProjectService

        async_session = get_async_session()

        async with async_session() as db:
            # 获取项目信息
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(project_id, user_id)

            if not project:
                raise ValueError(f"项目不存在: {project_id}")

            # 更新状态为处理中
            await project_service.update_processing_status(
                project_id=project_id,
                status=FileProcessingStatus.PROCESSING,
                progress=10.0,
                task_id=task_id
            )

            # 获取文件内容
            content = await _get_file_content(project, file_path, db)

            # 更新进度
            await project_service.update_processing_status(
                project_id=project_id,
                progress=50.0,
                task_id=task_id
            )

            # 分析文件内容
            analysis_result = await _analyze_file_content(
                content,
                SupportedFileType(project.file_type) if project.file_type else None
            )

            # 更新项目信息
            updates = {
                'word_count': analysis_result['word_count'],
                'total_paragraphs': analysis_result['paragraph_count'],
                'total_sentences': analysis_result['sentence_count'],
                'processing_progress': 90.0
            }

            # 对于Markdown文件，提取章节信息
            if project.file_type == SupportedFileType.MD and analysis_result.get('chapter_count'):
                updates['total_chapters'] = analysis_result['chapter_count']

            await project_service.update_project(project_id, **updates)

            # 更新处理状态为完成
            await project_service.update_processing_status(
                project_id=project_id,
                status=FileProcessingStatus.COMPLETED,
                progress=100.0,
                task_id=None
            )

            logger.info(f"文件处理完成: {task_id}")

            return {
                'success': True,
                'project_id': project_id,
                'analysis': analysis_result,
                'message': '文件处理完成'
            }

    try:
        return run_async_task(_process_file())

    except Exception as exc:
        logger.error(f"文件处理失败: {task_id}, 错误: {str(exc)}")
        logger.error(traceback.format_exc())

        # 更新处理状态为失败
        async def _update_error_status():
            from src.core.database import get_async_session

            async_session = get_async_session()

            async with async_session() as db:
                project_service = ProjectService(db)
                await project_service.update_processing_status(
                    project_id=project_id,
                    status=FileProcessingStatus.FAILED,
                    error_message=str(exc),
                    task_id=None
                )

        try:
            run_async_task(_update_error_status())
        except Exception as db_error:
            logger.error(f"更新项目状态失败: {db_error}")

        # 重试逻辑
        from src.utils.file_handlers import FileProcessingError
        from src.utils.storage import StorageError
        if isinstance(exc, (FileProcessingError, StorageError)) and self.request.retries < 3:
            raise self.retry(countdown=60 * (self.request.retries + 1), exc=exc)

        return {
            'success': False,
            'project_id': project_id,
            'error': str(exc),
            'message': '文件处理失败'
        }


@celery_app.task(bind=True, name='analyze_file_content')
def analyze_file_content(self, project_id: str, user_id: str) -> Dict[str, Any]:
    """
    分析文件内容（独立任务）

    Args:
        project_id: 项目ID
        user_id: 用户ID

    Returns:
        分析结果字典
    """
    task_id = self.request.id
    logger.info(f"开始分析文件内容: {task_id}, 项目ID: {project_id}")

    async def _analyze_content():
        from src.core.database import get_async_session

        async_session = get_async_session()

        async with async_session() as db:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(project_id, user_id)

            if not project:
                raise ValueError(f"项目不存在: {project_id}")

            # 从存储获取文件内容
            storage_client = await get_storage_client()
            content_bytes = await storage_client.download_file(project.minio_object_key)
            content = content_bytes.decode('utf-8', errors='ignore')

            # 分析内容
            analysis_result = await _analyze_file_content(
                content,
                SupportedFileType(project.file_type) if project.file_type else None
            )

            # 更新项目统计信息
            updates = {
                'word_count': analysis_result['word_count'],
                'total_paragraphs': analysis_result['paragraph_count'],
                'total_sentences': analysis_result['sentence_count'],
            }

            if project.file_type == SupportedFileType.MD and analysis_result.get('chapter_count'):
                updates['total_chapters'] = analysis_result['chapter_count']

            await project_service.update_project(project_id, **updates)

            logger.info(f"文件内容分析完成: {task_id}")

            return {
                'success': True,
                'project_id': project_id,
                'analysis': analysis_result,
                'message': '内容分析完成'
            }

    try:
        return run_async_task(_analyze_content())

    except Exception as exc:
        logger.error(f"文件内容分析失败: {task_id}, 错误: {str(exc)}")

        if self.request.retries < 2:
            raise self.retry(countdown=30, exc=exc)

        return {
            'success': False,
            'project_id': project_id,
            'error': str(exc),
            'message': '内容分析失败'
        }


@celery_app.task(name='extract_metadata')
def extract_metadata(project_id: str, user_id: str) -> Dict[str, Any]:
    """
    提取文件元数据

    Args:
        project_id: 项目ID
        user_id: 用户ID

    Returns:
        元数据字典
    """
    logger.info(f"开始提取元数据: 项目ID: {project_id}")

    async def _extract_meta():
        from src.core.database import get_async_session

        async_session = get_async_session()

        async with async_session() as db:
            project_service = ProjectService(db)
            project = await project_service.get_project_by_id(project_id, user_id)

            if not project:
                raise ValueError(f"项目不存在: {project_id}")

            metadata = {
                'file_size': project.file_size,
                'file_type': project.file_type,
                'original_filename': project.original_filename,
                'upload_time': project.created_at.isoformat() if project.created_at else None,
                'processing_time': project.updated_at.isoformat() if project.updated_at else None,
            }

            # 根据文件类型提取特定元数据
            if project.file_type == SupportedFileType.MD:
                metadata.update(_extract_markdown_metadata(project))
            elif project.file_type == SupportedFileType.DOCX:
                metadata.update(_extract_docx_metadata(project))
            elif project.file_type == SupportedFileType.EPUB:
                metadata.update(_extract_epub_metadata(project))

            return {
                'success': True,
                'project_id': project_id,
                'metadata': metadata,
                'message': '元数据提取完成'
            }

    try:
        return run_async_task(_extract_meta())

    except Exception as exc:
        logger.error(f"元数据提取失败: 项目ID: {project_id}, 错误: {str(exc)}")

        return {
            'success': False,
            'project_id': project_id,
            'error': str(exc),
            'message': '元数据提取失败'
        }


@celery_app.task(name='cleanup_temp_files')
def cleanup_temp_files(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    清理临时文件

    Args:
        max_age_hours: 最大保留时间（小时）

    Returns:
        清理结果字典
    """
    logger.info(f"开始清理临时文件，最大保留时间: {max_age_hours}小时")

    try:
        import time
        from datetime import datetime, timedelta

        temp_dir = Path(tempfile.gettempdir())
        cutoff_time = time.time() - (max_age_hours * 3600)

        cleaned_files = []
        cleaned_size = 0
        errors = []

        # 清理临时文件
        for temp_file in temp_dir.glob("aicg_upload_*"):
            try:
                if temp_file.stat().st_mtime < cutoff_time:
                    file_size = temp_file.stat().st_size
                    temp_file.unlink()
                    cleaned_files.append(str(temp_file))
                    cleaned_size += file_size
            except Exception as e:
                errors.append(f"清理文件失败 {temp_file}: {e}")

        # 清理空目录
        for temp_dir_item in temp_dir.glob("aicg_*"):
            try:
                if temp_dir_item.is_dir() and not any(temp_dir_item.iterdir()):
                    temp_dir_item.rmdir()
                    cleaned_files.append(f"目录: {temp_dir_item}")
            except Exception as e:
                errors.append(f"清理目录失败 {temp_dir_item}: {e}")

        logger.info(f"临时文件清理完成，清理了 {len(cleaned_files)} 个文件/目录，释放 {cleaned_size} 字节")

        return {
            'success': True,
            'cleaned_files': len(cleaned_files),
            'cleaned_size_bytes': cleaned_size,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2),
            'errors': errors,
            'message': '临时文件清理完成'
        }

    except Exception as exc:
        logger.error(f"临时文件清理失败: {str(exc)}")

        return {
            'success': False,
            'error': str(exc),
            'message': '临时文件清理失败'
        }


# 辅助函数
async def _get_file_content(project: Project, file_path: Optional[str], db) -> str:
    """获取文件内容"""
    if file_path and os.path.exists(file_path):
        # 从本地文件读取
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        # 从存储下载
        from src.utils.storage import get_storage_client
        storage_client = await get_storage_client()
        content_bytes = await storage_client.download_file(project.minio_object_key)
        return content_bytes.decode('utf-8', errors='ignore')


async def _analyze_file_content(content: str, file_type: Optional[SupportedFileType]) -> Dict[str, Any]:
    """分析文件内容"""
    if not content:
        return {
            'word_count': 0,
            'paragraph_count': 0,
            'sentence_count': 0,
            'chapter_count': 0,
            'character_count': 0
        }

    # 基础统计
    word_count = len(content.split())
    character_count = len(content)

    # 段落统计（简单实现：按空行分割）
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)

    # 句子统计（简单实现：按句号、问号、感叹号分割）
    import re
    sentences = re.split(r'[.!?。！？]+', content)
    sentence_count = len([s for s in sentences if s.strip()])

    result = {
        'word_count': word_count,
        'paragraph_count': paragraph_count,
        'sentence_count': sentence_count,
        'character_count': character_count,
        'chapter_count': 0
    }

    # 根据文件类型进行特定分析
    if file_type == SupportedFileType.MD:
        result['chapter_count'] = _count_markdown_chapters(content)

    return result


def _count_markdown_chapters(content: str) -> int:
    """统计Markdown文件中的章节数"""
    import re
    # 匹配 # ## ### 等标题
    headings = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)
    return len(headings)


def _extract_markdown_metadata(project: Project) -> Dict[str, Any]:
    """提取Markdown文件元数据"""
    metadata = {}

    if project.total_chapters:
        metadata['chapter_count'] = project.total_chapters
        metadata['has_toc'] = project.total_chapters > 1

    return metadata


def _extract_docx_metadata(project: Project) -> Dict[str, Any]:
    """提取Word文档元数据"""
    metadata = {
        'document_type': 'word_document'
    }

    # 可以在这里添加更多Word特定的元数据提取
    return metadata


def _extract_epub_metadata(project: Project) -> Dict[str, Any]:
    """提取EPUB电子书元数据"""
    metadata = {
        'document_type': 'epub_ebook'
    }

    # 可以在这里添加更多EPUB特定的元数据提取
    return metadata


# 定期任务
@celery_app.task(name='periodic_cleanup')
def periodic_cleanup():
    """定期清理任务"""
    cleanup_temp_files.delay()


# 配置定期任务
try:
    from celery.schedules import crontab

    celery_app.conf.beat_schedule = {
        'cleanup-temp-files': {
            'task': 'periodic_cleanup',
            'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        },
    }
except ImportError:
    logger.warning("Celery beat schedules not configured")


if __name__ == '__main__':
    celery_app.start()