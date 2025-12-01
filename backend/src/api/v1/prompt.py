"""
AI导演引擎 API

提供功能：
- 批量生成图像提示词
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.prompt import PromptGenerateRequest, PromptGenerateResponse, PromptGenerateByIdsRequest
from src.core.database import get_db
from src.core.exceptions import NotFoundError, BusinessLogicError
from src.core.logging import get_logger
from src.models.chapter import Chapter, ChapterStatus
from src.models.user import User
from src.services.project import ProjectService
from src.tasks.task import generate_prompts as generate_prompts_task, generate_prompts_by_ids

logger = get_logger(__name__)

router = APIRouter()


@router.post("/generate-prompts", response_model=PromptGenerateResponse)
async def generate_prompts(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        request: PromptGenerateRequest
):
    """
    为章节批量生成提示词
    
    根据章节内容，调用LLM为每个句子生成专业的图像提示词。
    """
    # 1. 获取章节并验证权限
    stmt = select(Chapter).where(Chapter.id == request.chapter_id)
    result = await db.execute(stmt)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise NotFoundError(
            "章节不存在",
            resource_type="chapter",
            resource_id=str(request.chapter_id)
        )

    # 验证项目权限
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    # 2. 投递任务到celery
    result = generate_prompts_task.delay(chapter.id.hex, request.api_key_id.hex, request.style, request.model, request.custom_prompt)

    # 3.更新章节状态为提示词生成中
    chapter.status = "generating_prompts"
    await db.flush()
    await db.commit()

    logger.info(f"成功为章节 {request.chapter_id} 投递提示词生成任务，任务ID: {result.id}")
    return PromptGenerateResponse(success=True, message="提示词生成任务已提交", task_id=result.id)


@router.post("/generate-prompts-ids", response_model=PromptGenerateResponse)
async def generate_prompts(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        request: PromptGenerateByIdsRequest
):
    """
    根据ids列表为句子批量生成提示词

    根据句子ID列表，调用LLM为每个句子生成专业的图像提示词。
    """

    # 1. 投递任务到celery
    result = generate_prompts_by_ids.delay(request.sentence_ids, request.api_key_id.hex, request.style, request.model, request.custom_prompt)

    logger.info(f"成功为章节 {request.sentence_ids} 投递提示词生成任务，任务ID: {result.id}")
    return PromptGenerateResponse(success=True, message="提示词生成任务已提交，请稍后查看结果。", task_id=result.id)


__all__ = ["router"]
