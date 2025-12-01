"""
文件处理 Celery 任务模块 - 专注于 Celery 任务定义

该模块仅包含 Celery 任务定义和配置，具体的业务逻辑实现
已迁移到 src.services.project_processing 模块中。

职责：
- Celery 应用配置
- 任务定义和装饰器
- 任务参数验证
- 错误处理和重试策略
- 任务状态管理
"""

import asyncio
from typing import Any, Dict, List

from celery import Celery

from src.core.config import settings
from src.core.logging import get_logger
from src.services.project_processing import project_processing_service
from src.services.prompt import prompt_service
from src.services.image import image_service

logger = get_logger(__name__)

# ---------------------------
# Celery 实例与配置
# ---------------------------

celery_app = Celery(
    "file_processing",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=getattr(settings, "CELERY_TASK_TIME_LIMIT", 600),
    task_soft_time_limit=getattr(settings, "CELERY_TASK_SOFT_TIME_LIMIT", 480),
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
)


# ---------------------------
# Celery 任务定义
# ---------------------------

@celery_app.task(
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="file_processing.process_uploaded_file"
)
def process_uploaded_file(self, project_id: str, owner_id: str) -> Dict[str, Any]:
    """
    处理上传文件的 Celery 任务

    该任务仅负责调用服务层的文件处理逻辑，不包含任何业务逻辑。
    所有的文件处理、状态管理、错误处理都在服务层完成。

    Args:
        project_id: 项目ID
        owner_id: 项目所有者ID

    Returns:
        Dict[str, Any]: 处理结果

    Raises:
        Exception: 当处理失败且需要重试时抛出异常
    """
    logger.info(f"Celery任务开始: process_uploaded_file (project_id={project_id})")

    # 使用辅助函数运行异步任务
    result = run_async_task(project_processing_service.process_file_task(project_id, owner_id))

    logger.info(f"Celery任务成功: process_uploaded_file (project_id={project_id})")
    return result


def run_async_task(coro):
    """
    运行异步任务的辅助函数，确保在新的事件循环中重置数据库连接
    
    Args:
        coro: 要运行的协程对象
        
    Returns:
        协程的执行结果
    """

    async def _wrapper():
        from src.core.database import close_database_connections
        # 在新的事件循环中，必须重置数据库连接，因为旧的连接绑定在已关闭的循环上
        await close_database_connections()
        return await coro

    return asyncio.run(_wrapper())


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="file_processing.retry_failed_project"
)
def retry_failed_project(self, project_id: str, owner_id: str) -> Dict[str, Any]:
    """
    重试失败项目的 Celery 任务

    该任务仅负责调用服务层的重试逻辑，不包含业务逻辑。

    Args:
        project_id: 项目ID
        owner_id: 项目所有者ID

    Returns:
        Dict[str, Any]: 重试结果
    """
    logger.info(f"Celery任务开始: retry_failed_project (project_id={project_id})")

    try:
        # 使用辅助函数运行异步任务
        result = run_async_task(project_processing_service.retry_failed_project(project_id, owner_id))

        if result.get("success", False):
            logger.info(f"Celery任务成功: retry_failed_project (project_id={project_id})")
        else:
            logger.error(
                f"Celery任务失败: retry_failed_project (project_id={project_id}, error={result.get('message')})")

        return result

    except Exception as e:
        logger.error(f"Celery任务异常: retry_failed_project (project_id={project_id}, error={e})", exc_info=True)
        raise


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="generate.generate_prompts"
)
def generate_prompts(self, chapter_id: str, api_key_id: str, style: str, model: str = None, custom_prompt: str = None):
    """
    为章节生成提示词的 Celery 任务

    该任务仅负责调用服务层的提示词生成逻辑，不包含业务逻辑。

    Args:
        chapter_id: 章节ID
        api_key_id: API密钥ID
        style: 提示词风格
        model: 模型名称
        custom_prompt: 自定义系统提示词

    Returns:
        Dict[str, Any]: 生成结果，包含统计信息
    """
    logger.info(f"Celery任务开始: generate_prompts (chapter_id={chapter_id})")
    result = run_async_task(prompt_service.generate_prompts_batch(chapter_id, api_key_id, style, model, custom_prompt))
    logger.info(f"Celery任务成功: generate_prompts (chapter_id={chapter_id})")
    return result


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="generate.generate_prompts_by_ids"
)
def generate_prompts_by_ids(self, sentence_ids: List[str], api_key_id: str, style: str, model: str = None, custom_prompt: str = None):
    """
    为章节生成提示词的 Celery 任务

    该任务仅负责调用服务层的提示词生成逻辑，不包含业务逻辑。

    Args:
        sentence_ids: 句子ID列表
        api_key_id: API密钥ID
        style: 提示词风格
        model: 模型名称
        custom_prompt: 自定义系统提示词

    Returns:
        Dict[str, Any]: 生成结果
    """
    logger.info(f"Celery任务开始: generate_prompts_by_ids (sentence_ids={sentence_ids})")
    result = run_async_task(prompt_service.generate_prompts_by_ids(sentence_ids, api_key_id, style, model, custom_prompt))
    logger.info(f"Celery任务成功: generate_prompts_by_ids (chapter_id={sentence_ids})")
    return result


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="generate.generate_images"
)
def generate_images(self, api_key_id: str, sentences_ids: list[str]):
    """
    为章节或指定句子批量生成图片的 Celery 任务

    该任务仅负责调用服务层的图片生成逻辑，不包含业务逻辑。

    Args:
        api_key_id: API密钥ID
        sentences_ids: 句子ID列表（可选，与chapter_id二选一）

    Returns:
        Dict[str, Any]: 生成结果，包含统计信息
    """

    logger.info(f"Celery任务开始: generate_images (sentences_ids={sentences_ids})")

    result = run_async_task(image_service.generate_images(api_key_id, sentences_ids))
    logger.info(f"Celery任务成功: generate_images (sentences_ids={sentences_ids})")
    return result


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="generate.generate_audio"
)
def generate_audio(self, api_key_id: str, sentences_ids: list[str], voice: str = "alloy", model: str = "tts-1"):
    """
    为章节或指定句子批量生成音频的 Celery 任务

    该任务仅负责调用服务层的音频生成逻辑，不包含业务逻辑。

    Args:
        api_key_id: API密钥ID
        sentences_ids: 句子ID列表
        voice: 语音风格
        model: 模型名称

    Returns:
        Dict[str, Any]: 生成结果，包含统计信息
    """
    from src.services.audio import audio_service

    logger.info(f"Celery任务开始: generate_audio (sentences_ids={sentences_ids})")

    result = run_async_task(audio_service.generate_audio(api_key_id, sentences_ids, voice, model))
    logger.info(f"Celery任务成功: generate_audio (sentences_ids={sentences_ids})")
    return result


# ---------------------------
# 导出的任务列表
# ---------------------------

__all__ = [
    'celery_app',
    'process_uploaded_file',
    'retry_failed_project',
    'generate_prompts',
    'generate_images',
    'generate_audio'
]
