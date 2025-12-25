"""
电影过渡视频相关API路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.api.dependencies import get_current_user_required
from src.api.schemas.movie import TransitionGenerateRequest, TransitionResponse, TransitionUpdateRequest

logger = get_logger(__name__)
router = APIRouter()

@router.get("/scripts/{script_id}/transitions", summary="获取剧本的过渡列表")
async def get_transitions(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """获取剧本的所有过渡视频记录（包含分镜和场景信息）"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from src.models.movie import MovieShotTransition, MovieShot, MovieScene
    
    # 查询该剧本的所有过渡，预加载关联的分镜和场景信息
    stmt = (
        select(MovieShotTransition)
        .where(MovieShotTransition.script_id == script_id)
        .options(
            selectinload(MovieShotTransition.from_shot).selectinload(MovieShot.scene),
            selectinload(MovieShotTransition.to_shot).selectinload(MovieShot.scene)
        )
        .order_by(MovieShotTransition.order_index)
    )
    result = await db.execute(stmt)
    transitions = result.scalars().all()
    
    # 格式化返回数据，包含分镜和场景信息
    from datetime import timedelta
    from src.utils.storage import get_storage_client
    
    storage_client = await get_storage_client()
    
    transition_list = []
    for t in transitions:
        # 转换video_url为presigned URL
        video_url = None
        if t.video_url:
            try:
                video_url = storage_client.get_presigned_url(t.video_url, expires=timedelta(hours=1))
            except Exception as e:
                logger.warning(f"获取视频URL失败: {e}")
                video_url = t.video_url
        
        transition_data = {
            "id": str(t.id),
            "script_id": str(t.script_id),
            "from_shot_id": str(t.from_shot_id),
            "to_shot_id": str(t.to_shot_id),
            "order_index": t.order_index,
            "video_prompt": t.video_prompt,
            "video_url": video_url,
            "video_task_id": t.video_task_id,
            "status": t.status,
            "error_message": t.error_message,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            # 添加分镜信息
            "from_shot": {
                "shot": t.from_shot.shot if t.from_shot else None,
                "dialogue": t.from_shot.dialogue if t.from_shot else None,
                "scene_name": t.from_shot.scene.scene if (t.from_shot and t.from_shot.scene) else None,
                "scene_order": t.from_shot.scene.order_index if (t.from_shot and t.from_shot.scene) else None,
            } if t.from_shot else None,
            "to_shot": {
                "shot": t.to_shot.shot if t.to_shot else None,
                "dialogue": t.to_shot.dialogue if t.to_shot else None,
                "scene_name": t.to_shot.scene.scene if (t.to_shot and t.to_shot.scene) else None,
                "scene_order": t.to_shot.scene.order_index if (t.to_shot and t.to_shot.scene) else None,
            } if t.to_shot else None,
        }
        transition_list.append(transition_data)
    
    return {"transitions": transition_list}

@router.get("/transitions/{transition_id}", summary="获取单个过渡")
async def get_transition(
    transition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """获取单个过渡视频记录"""
    from datetime import timedelta
    from src.utils.storage import get_storage_client
    from src.models.movie import MovieShotTransition
    
    transition = await db.get(MovieShotTransition, transition_id)
    if not transition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="过渡不存在")
    
    # 转换video_url为presigned URL
    video_url = None
    if transition.video_url:
        try:
            storage_client = await get_storage_client()
            video_url = storage_client.get_presigned_url(transition.video_url, expires=timedelta(hours=1))
        except Exception as e:
            logger.warning(f"获取视频URL失败: {e}")
            video_url = transition.video_url
    
    return {
        "id": str(transition.id),
        "script_id": str(transition.script_id),
        "from_shot_id": str(transition.from_shot_id),
        "to_shot_id": str(transition.to_shot_id),
        "order_index": transition.order_index,
        "video_prompt": transition.video_prompt,
        "video_url": video_url,
        "video_task_id": transition.video_task_id,
        "status": transition.status,
        "error_message": transition.error_message,
        "created_at": transition.created_at.isoformat() if transition.created_at else None,
        "updated_at": transition.updated_at.isoformat() if transition.updated_at else None
    }

@router.put("/transitions/{transition_id}", summary="更新过渡提示词")
async def update_transition(
    transition_id: str,
    req: TransitionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """更新过渡视频提示词"""
    from src.models.movie import MovieShotTransition
    
    transition = await db.get(MovieShotTransition, transition_id)
    if not transition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="过渡不存在")
    
    transition.video_prompt = req.video_prompt
    await db.commit()
    await db.refresh(transition)
    
    return transition

@router.delete("/transitions/{transition_id}", summary="删除过渡")
async def delete_transition(
    transition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """删除单个过渡视频记录"""
    from src.models.movie import MovieShotTransition
    
    transition = await db.get(MovieShotTransition, transition_id)
    if not transition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="过渡不存在")
    
    await db.delete(transition)
    await db.commit()
    
    return {"message": "删除成功"}

@router.post("/scripts/{script_id}/create-transitions", summary="创建过渡视频记录")
async def create_transitions(
    script_id: str,
    req: TransitionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """
    为剧本的所有连续分镜创建过渡视频记录
    包含视频提示词生成
    """
    from src.tasks.movie import movie_create_transitions
    task = movie_create_transitions.delay(script_id, req.api_key_id, req.model)
    return {"task_id": task.id, "message": "过渡视频创建任务已提交"}

@router.post("/scripts/{script_id}/generate-transition-videos", summary="批量生成过渡视频")
async def generate_transition_videos(
    script_id: str,
    req: TransitionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """批量生成剧本所有过渡视频"""
    from src.tasks.movie import movie_generate_transition_videos
    task = movie_generate_transition_videos.delay(script_id, req.api_key_id, req.video_model)
    return {"task_id": task.id, "message": "过渡视频生成任务已提交"}

@router.post("/transitions/{transition_id}/generate-video", summary="生成单个过渡视频")
async def generate_single_transition_video(
    transition_id: str,
    req: TransitionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """生成单个过渡视频（支持自定义提示词）"""
    from src.tasks.movie import movie_generate_single_transition
    # 如果提供了自定义提示词，先更新
    if req.prompt:
        from src.models.movie import MovieShotTransition
        transition = await db.get(MovieShotTransition, transition_id)
        if transition:
            transition.video_prompt = req.prompt
            await db.commit()
    
    task = movie_generate_single_transition.delay(transition_id, req.api_key_id, req.video_model)
    return {"task_id": task.id, "message": "过渡视频生成任务已提交"}
