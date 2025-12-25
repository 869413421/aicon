"""
过渡视频状态同步任务
"""
import asyncio
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import get_logger
from src.models.movie import MovieShotTransition
from src.services.provider.vector_engine_provider import VectorEngineProvider
from src.services.api_key import APIKeyService
from src.core.storage import storage_client
from src.tasks.base import async_task_decorator
from src.tasks.app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.sync_transition_video_status"
)
@async_task_decorator
async def sync_transition_video_status(db_session: AsyncSession, self):
    """
    同步所有处理中的过渡视频任务状态
    """
    logger.info("开始同步过渡视频任务状态")
    
    # 查询所有processing状态的过渡
    stmt = select(MovieShotTransition).where(
        MovieShotTransition.status == "processing",
        MovieShotTransition.video_task_id.isnot(None)
    )
    result = await db_session.execute(stmt)
    transitions = result.scalars().all()
    
    if not transitions:
        logger.info("没有需要同步的过渡视频任务")
        return {"synced": 0, "completed": 0, "failed": 0}
    
    logger.info(f"找到 {len(transitions)} 个待同步的过渡视频任务")
    
    synced_count = 0
    completed_count = 0
    failed_count = 0
    
    # 按API Key分组
    transitions_by_key = {}
    for transition in transitions:
        # 需要获取API Key，这里简化处理，假设使用同一个key
        # 实际应该从transition关联的script获取
        task_id = transition.video_task_id
        if task_id not in transitions_by_key:
            transitions_by_key[task_id] = transition
    
    # TODO: 需要获取正确的API Key
    # 这里需要重构以支持多个API Key
    api_key_service = APIKeyService(db_session)
    
    for task_id, transition in transitions_by_key.items():
        try:
            # 这里需要获取正确的API Key
            # 暂时跳过，需要完善
            logger.warning(f"跳过任务 {task_id}，需要完善API Key获取逻辑")
            continue
            
        except Exception as e:
            logger.error(f"同步任务 {task_id} 失败: {e}")
            failed_count += 1
    
    await db_session.commit()
    
    logger.info(f"同步完成: 总计 {synced_count}, 完成 {completed_count}, 失败 {failed_count}")
    return {
        "synced": synced_count,
        "completed": completed_count,
        "failed": failed_count
    }
