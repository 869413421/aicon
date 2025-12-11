"""
Bilibili发布Celery任务
"""

from typing import Dict, Any

from src.core.logging import get_logger
from src.tasks.task import celery_app, run_async_task

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="bilibili.upload_chapter"
)
def upload_chapter_to_bilibili(
    self,
    publish_task_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    上传章节视频到B站的 Celery 任务
    
    该任务仅负责调用服务层的上传逻辑,不包含业务逻辑。
    
    Args:
        self: Celery任务实例
        publish_task_id: 发布任务ID
        user_id: 用户ID
        
    Returns:
        Dict[str, Any]: 上传结果
    """
    logger.info(f"Celery任务开始: upload_chapter_to_bilibili (publish_task_id={publish_task_id})")
    
    # 使用辅助函数运行异步任务
    from src.services.bilibili import bilibili_publish_service
    
    async def _run_upload():
        async with bilibili_publish_service:
            return await bilibili_publish_service.upload_chapter_task(
                publish_task_id=publish_task_id,
                user_id=user_id,
                celery_task_id=self.request.id
            )
    
    result = run_async_task(_run_upload())
    
    logger.info(f"Celery任务完成: upload_chapter_to_bilibili (publish_task_id={publish_task_id})")
    return result


__all__ = [
    "upload_chapter_to_bilibili",
]
