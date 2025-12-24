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
    """获取剧本的所有过渡视频记录"""
    from sqlalchemy import select
    from src.models.movie import MovieShotTransition
    
    # 查询该剧本的所有过渡
    stmt = select(MovieShotTransition).where(MovieShotTransition.script_id == script_id).order_by(MovieShotTransition.order_index)
    result = await db.execute(stmt)
    transitions = result.scalars().all()
    
    return {"transitions": transitions}

@router.get("/transitions/{transition_id}", summary="获取单个过渡")
async def get_transition(
    transition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """获取单个过渡视频记录"""
    from src.models.movie import MovieShotTransition
    
    transition = await db.get(MovieShotTransition, transition_id)
    if not transition:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="过渡不存在")
    
    return transition

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
