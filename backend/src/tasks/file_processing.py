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
from typing import Any, Dict

from celery import Celery

from src.core.config import settings
from src.core.logging import get_logger
from src.services.project_processing import project_processing_service

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

    # 使用asyncio.run运行异步函数
    result = asyncio.run(project_processing_service.process_file_task(project_id, owner_id))

    logger.info(f"Celery任务成功: process_uploaded_file (project_id={project_id})")
    return result


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
        # 使用asyncio.run运行异步函数
        result = asyncio.run(project_processing_service.retry_failed_project(project_id, owner_id))

        if result.get("success", False):
            logger.info(f"Celery任务成功: retry_failed_project (project_id={project_id})")
        else:
            logger.error(f"Celery任务失败: retry_failed_project (project_id={project_id}, error={result.get('message')})")

        return result

    except Exception as e:
        logger.error(f"Celery任务异常: retry_failed_project (project_id={project_id}, error={e})", exc_info=True)
        raise


# ---------------------------
# 导出的任务列表
# ---------------------------

__all__ = [
    'celery_app',
    'process_uploaded_file',
    'retry_failed_project',
]
