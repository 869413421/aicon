"""
Bilibili发布API端点
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.bilibili import (
    LoginResponse,
    PublishRequest,
    PublishResponse,
    PublishTaskStatus,
    TidOption
)
from src.core.database import get_db
from src.models.publish_task import BilibiliAccount, PublishTask
from src.models.user import User
from src.services.bilibili import BilibiliService
from src.tasks.bilibili_task import upload_chapter_to_bilibili

router = APIRouter()


@router.post("/login/qrcode", response_model=LoginResponse)
async def login_by_qrcode(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """二维码登录B站"""
    bilibili_service = BilibiliService(db)
    result = await bilibili_service.login_by_qrcode(str(current_user.id))
    
    # 如果登录成功,保存账号信息
    if result["success"]:
        # 检查是否已存在账号
        query = select(BilibiliAccount).where(
            BilibiliAccount.user_id == current_user.id
        )
        existing_result = await db.execute(query)
        account = existing_result.scalar_one_or_none()
        
        if account:
            # 更新现有账号
            account.cookie_path = result["cookie_file"]
            account.last_login_at = datetime.utcnow()
        else:
            # 创建新账号
            from datetime import datetime
            account = BilibiliAccount(
                user_id=current_user.id,
                account_name=f"B站账号_{current_user.username}",
                cookie_path=result["cookie_file"],
                last_login_at=datetime.utcnow()
            )
            db.add(account)
        
        await db.commit()
    
    return LoginResponse(**result)


@router.post("/publish", response_model=PublishResponse)
async def publish_to_bilibili(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        request: PublishRequest
):
    """发布视频到B站"""
    
    # 验证章节是否存在
    from src.models.chapter import Chapter
    query = select(Chapter).where(Chapter.id == request.chapter_id)
    result = await db.execute(query)
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    if not chapter.video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="章节视频未生成"
        )
    
    # 创建发布任务
    publish_task = PublishTask(
        chapter_id=chapter.id,
        user_id=current_user.id,
        platform="bilibili",
        title=request.title,
        desc=request.desc,
        tid=request.tid,
        tag=request.tag,
        copyright=request.copyright,
        source=request.source,
        dynamic=request.dynamic,
        cover_url=request.cover_url,
        dtime=request.dtime,
        upload_line=request.upload_line,
        upload_limit=request.upload_limit
    )
    
    db.add(publish_task)
    await db.commit()
    await db.refresh(publish_task)
    
    # 投递Celery任务
    task = upload_chapter_to_bilibili.delay(
        publish_task_id=str(publish_task.id),
        user_id=str(current_user.id)
    )
    
    # 更新任务ID
    publish_task.celery_task_id = task.id
    await db.commit()
    
    return PublishResponse(
        success=True,
        task_id=task.id,
        publish_task_id=str(publish_task.id),
        message="发布任务已提交"
    )


@router.get("/tasks/{task_id}", response_model=PublishTaskStatus)
async def get_publish_task_status(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        task_id: str
):
    """获取发布任务状态"""
    query = select(PublishTask).where(
        PublishTask.id == task_id,
        PublishTask.user_id == current_user.id
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return PublishTaskStatus(
        id=str(task.id),
        chapter_id=str(task.chapter_id),
        platform=task.platform,
        title=task.title,
        status=task.status,
        progress=task.progress,
        bvid=task.bvid,
        aid=task.aid,
        error_message=task.error_message,
        created_at=task.created_at,
        published_at=task.published_at
    )


@router.get("/tasks", response_model=List[PublishTaskStatus])
async def get_publish_tasks(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        chapter_id: str = None,
        status_filter: str = None,
        limit: int = 20
):
    """获取发布任务列表"""
    query = select(PublishTask).where(
        PublishTask.user_id == current_user.id
    )
    
    if chapter_id:
        query = query.where(PublishTask.chapter_id == chapter_id)
    
    if status_filter:
        query = query.where(PublishTask.status == status_filter)
    
    query = query.order_by(PublishTask.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        PublishTaskStatus(
            id=str(task.id),
            chapter_id=str(task.chapter_id),
            platform=task.platform,
            title=task.title,
            status=task.status,
            progress=task.progress,
            bvid=task.bvid,
            aid=task.aid,
            error_message=task.error_message,
            created_at=task.created_at,
            published_at=task.published_at
        )
        for task in tasks
    ]


@router.get("/tid-options", response_model=List[TidOption])
async def get_tid_options():
    """获取B站分区选项"""
    return [
        TidOption(label="知识", value=36),
        TidOption(label="科技", value=188),
        TidOption(label="生活", value=160),
        TidOption(label="游戏", value=4),
        TidOption(label="娱乐", value=5),
        TidOption(label="影视", value=181),
        TidOption(label="音乐", value=3),
        TidOption(label="动画", value=1),
        TidOption(label="时尚", value=155),
        TidOption(label="美食", value=211),
        TidOption(label="汽车", value=223),
        TidOption(label="运动", value=234),
        TidOption(label="动物圈", value=217),
        TidOption(label="舞蹈", value=129),
        TidOption(label="国创", value=167),
        TidOption(label="鬼畜", value=119),
    ]


__all__ = ["router"]
