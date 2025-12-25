"""
电影制作相关的 Celery 任务
"""
from typing import Any, Dict, List
from src.tasks.app import celery_app
from src.tasks.base import async_task_decorator
from src.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.extract_scenes"
)
@async_task_decorator
async def movie_extract_scenes(db_session: AsyncSession, self, chapter_id: str, api_key_id: str, model: str = None):
    """从章节提取场景的 Celery 任务"""
    from src.services.scene_service import SceneService
    logger.info(f"Celery任务开始: movie_extract_scenes (chapter_id={chapter_id})")
    
    async def on_progress(percent, msg):
        self.update_state(state='PROGRESS', meta={'percent': percent, 'message': msg})
        
    service = SceneService(db_session)
    result = await service.extract_scenes_from_chapter(chapter_id, api_key_id, model, on_progress=on_progress)
    
    logger.info(f"Celery任务完成: movie_extract_scenes")
    return {"script_id": str(result.id)}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.extract_shots"
)
@async_task_decorator
async def movie_extract_shots(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """从剧本提取分镜的 Celery 任务"""
    from src.services.storyboard_service import StoryboardService
    logger.info(f"Celery任务开始: movie_extract_shots (script_id={script_id})")
    
    service = StoryboardService(db_session)
    result = await service.batch_extract_shots_from_script(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_extract_shots, 成功 {result['success']}, 失败 {result['failed']}")
    return result

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.create_transitions"
)
@async_task_decorator
async def movie_create_transitions(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """创建过渡视频记录的 Celery 任务"""
    from src.services.transition_service import TransitionService
    logger.info(f"Celery任务开始: movie_create_transitions (script_id={script_id})")
    
    service = TransitionService(db_session)
    result = await service.batch_create_transitions(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_create_transitions, 成功 {result['success']}")
    return result

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.extract_characters"
)
@async_task_decorator
async def movie_extract_characters(db_session: AsyncSession, self, chapter_id: str, api_key_id: str, model: str = None):
    """从章节提取角色的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    logger.info(f"Celery任务开始: movie_extract_characters (chapter_id={chapter_id})")
    
    service = MovieCharacterService(db_session)
    chars = await service.extract_characters_from_chapter(chapter_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_extract_characters, extracted {len(chars)} characters")
    return {"character_count": len(chars)}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_character_avatar"
)
@async_task_decorator
async def movie_generate_character_avatar(db_session: AsyncSession, self, character_id: str, api_key_id: str, model: str = None, prompt: str = None, style: str = "cinematic"):
    """生成角色头像的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    logger.info(f"Celery任务开始: movie_generate_character_avatar (character_id={character_id})")
    
    service = MovieCharacterService(db_session)
    url = await service.generate_character_avatar(character_id, api_key_id, model, prompt, style)
    
    logger.info(f"Celery任务完成: movie_generate_character_avatar")
    return {"avatar_url": url}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_keyframes"
)
@async_task_decorator
async def movie_generate_keyframes(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """批量生成关键帧的 Celery 任务"""
    from src.services.visual_identity_service import VisualIdentityService
    logger.info(f"Celery任务开始: movie_generate_keyframes (script_id={script_id})")
    
    service = VisualIdentityService(db_session)
    stats = await service.batch_generate_keyframes(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_generate_keyframes")
    return stats

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_single_keyframe"
)
@async_task_decorator
async def movie_generate_single_keyframe(db_session: AsyncSession, self, shot_id: str, api_key_id: str, model: str = None, prompt: str = None):
    """生成单个分镜关键帧的 Celery 任务"""
    from src.services.visual_identity_service import VisualIdentityService
    logger.info(f"Celery任务开始: movie_generate_single_keyframe (shot_id={shot_id})")
    
    service = VisualIdentityService(db_session)
    url = await service.generate_single_keyframe(shot_id, api_key_id, model, prompt)
    
    logger.info(f"Celery任务完成: movie_generate_single_keyframe")
    return {"success": True}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_transition_videos"
)
@async_task_decorator
async def movie_generate_transition_videos(db_session: AsyncSession, self, script_id: str, api_key_id: str, video_model: str):
    """批量生成过渡视频的 Celery 任务"""
    from src.services.transition_service import TransitionService
    logger.info(f"Celery任务开始: movie_generate_transition_videos (script_id={script_id})")
    
    service = TransitionService(db_session)
    # TODO: 实现批量生成逻辑
    result = {"success": 0, "failed": 0, "message": "批量生成功能待实现"}
    
    logger.info(f"Celery任务完成: movie_generate_transition_videos")
    return result

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_single_transition"
)
@async_task_decorator
async def movie_generate_single_transition(db_session: AsyncSession, self, transition_id: str, api_key_id: str, video_model: str):
    """生成单个过渡视频的 Celery 任务"""
    from src.services.transition_service import TransitionService
    logger.info(f"Celery任务开始: movie_generate_single_transition (transition_id={transition_id})")
    
    service = TransitionService(db_session)
    task_id = await service.generate_transition_video(transition_id, api_key_id, video_model)
    
    logger.info(f"Celery任务完成: movie_generate_single_transition, task_id={task_id}")
    return {"success": True, "video_task_id": task_id}

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.sync_transition_video_status"
)
@async_task_decorator
async def sync_transition_video_status(db_session: AsyncSession, self, api_key_id: str):
    """
    同步过渡视频任务状态（定时任务）
    
    Args:
        api_key_id: API Key ID
    """
    from src.services.transition_service import TransitionService
    logger.info(f"Celery任务开始: sync_transition_video_status")
    
    service = TransitionService(db_session)
    result = await service.sync_transition_video_status(api_key_id)
    
    logger.info(f"Celery任务完成: sync_transition_video_status, 结果: {result}")
    return result

# Removed: sync_all_video_task_status - obsolete, replaced by transition video status sync

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.batch_generate_avatars"
)
@async_task_decorator
async def movie_batch_generate_avatars(db_session: AsyncSession, self, project_id: str, api_key_id: str, model: str = None):
    """批量生成角色头像的 Celery 任务"""
    from src.services.movie_character_service import MovieCharacterService
    
    logger.info(f"Celery任务开始: movie_batch_generate_avatars (project_id={project_id})")
    
    service = MovieCharacterService(db_session)
    result = await service.batch_generate_avatars(project_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_batch_generate_avatars, 成功: {result['success']}, 失败: {result['failed']}")
    return result

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_scene_images"
)
@async_task_decorator
async def movie_generate_scene_images(db_session: AsyncSession, self, script_id: str, api_key_id: str, model: str = None):
    """批量生成场景图的 Celery 任务"""
    from src.services.scene_image_service import SceneImageService
    logger.info(f"Celery任务开始: movie_generate_scene_images (script_id={script_id})")
    
    service = SceneImageService(db_session)
    stats = await service.batch_generate_scene_images(script_id, api_key_id, model)
    
    logger.info(f"Celery任务完成: movie_generate_scene_images, 成功 {stats['success']}, 失败 {stats['failed']}")
    return stats

@celery_app.task(
    bind=True,
    max_retries=0,
    name="movie.generate_single_scene_image"
)
@async_task_decorator
async def movie_generate_single_scene_image(db_session: AsyncSession, self, scene_id: str, api_key_id: str, model: str = None, prompt: str = None):
    """生成单个场景图的 Celery 任务"""
    from src.services.scene_image_service import SceneImageService
    logger.info(f"Celery任务开始: movie_generate_single_scene_image (scene_id={scene_id})")
    
    service = SceneImageService(db_session)
    url = await service.generate_scene_image(scene_id, api_key_id, model, prompt)
    
    logger.info(f"Celery任务完成: movie_generate_single_scene_image")
    return {"scene_image_url": url}
