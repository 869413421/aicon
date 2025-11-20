"""
段落管理API - 使用schemas模块中的Pydantic模型
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.paragraph import (
    ParagraphBatchUpdate,
    ParagraphCreate,
    ParagraphDeleteResponse,
    ParagraphListResponse,
    ParagraphResponse,
    ParagraphUpdate,
)
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.services.chapter import ChapterService
from src.services.paragraph import ParagraphService
from src.services.project import ProjectService

logger = get_logger(__name__)

router = APIRouter()


@router.get("/chapters/{chapter_id}/paragraphs", response_model=ParagraphListResponse)
async def get_chapter_paragraphs(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        chapter_id: str
):
    """获取章节的所有段落"""
    paragraph_service = ParagraphService(db)
    chapter_service = ChapterService(db)

    # 获取章节并验证权限
    chapter = await chapter_service.get_chapter_by_id(chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    # 获取段落列表
    paragraphs = await paragraph_service.get_chapter_paragraphs(chapter_id)

    # 转换为响应模型
    paragraph_responses = [ParagraphResponse.from_dict(p.to_dict()) for p in paragraphs]

    return ParagraphListResponse(
        paragraphs=paragraph_responses,
        total=len(paragraphs),
        page=1,
        size=len(paragraphs),
        total_pages=1
    )


@router.get("/{paragraph_id}", response_model=ParagraphResponse)
async def get_paragraph(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        paragraph_id: str
):
    """获取段落详情"""
    paragraph_service = ParagraphService(db)
    paragraph = await paragraph_service.get_paragraph_by_id(paragraph_id)

    # 验证项目权限
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_id(paragraph.chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    return ParagraphResponse.from_dict(paragraph.to_dict())


@router.post("/chapters/{chapter_id}/paragraphs", response_model=ParagraphResponse)
async def create_paragraph(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        chapter_id: str,
        paragraph_data: ParagraphCreate
):
    """创建新段落并自动解析句子"""
    paragraph_service = ParagraphService(db)
    chapter_service = ChapterService(db)

    # 获取章节并验证权限
    chapter = await chapter_service.get_chapter_by_id(chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    # 创建段落
    paragraph = await paragraph_service.create_paragraph(
        chapter_id=chapter_id,
        content=paragraph_data.content,
        order_index=paragraph_data.order_index
    )

    return ParagraphResponse.from_dict(paragraph.to_dict())


@router.put("/{paragraph_id}", response_model=ParagraphResponse)
async def update_paragraph(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        paragraph_id: str,
        paragraph_data: ParagraphUpdate
):
    """更新段落信息，如果内容变更则重新解析句子"""
    paragraph_service = ParagraphService(db)

    # 获取段落并验证权限
    paragraph = await paragraph_service.get_paragraph_by_id(paragraph_id)
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_id(paragraph.chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    # 准备更新数据
    updates = {}
    if paragraph_data.content is not None:
        updates['content'] = paragraph_data.content
    if paragraph_data.action is not None:
        updates['action'] = paragraph_data.action
    if paragraph_data.edited_content is not None:
        updates['edited_content'] = paragraph_data.edited_content
    if paragraph_data.ignore_reason is not None:
        updates['ignore_reason'] = paragraph_data.ignore_reason

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供更新字段"
        )

    # 更新段落
    updated_paragraph = await paragraph_service.update_paragraph(
        paragraph_id=paragraph_id,
        chapter_id=paragraph.chapter_id,
        **updates
    )

    return ParagraphResponse.from_dict(updated_paragraph.to_dict())


@router.put("/chapters/{chapter_id}/paragraphs/batch", response_model=List[ParagraphResponse])
async def batch_update_paragraphs(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        chapter_id: str,
        batch_data: ParagraphBatchUpdate
):
    """批量更新段落"""
    paragraph_service = ParagraphService(db)
    chapter_service = ChapterService(db)

    # 获取章节并验证权限
    chapter = await chapter_service.get_chapter_by_id(chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    updated_paragraphs = []

    for item in batch_data.paragraphs:
        # 准备更新数据
        updates = {}
        if item.content is not None:
            updates['content'] = item.content
        if item.action is not None:
            updates['action'] = item.action
        if item.edited_content is not None:
            updates['edited_content'] = item.edited_content
        if item.ignore_reason is not None:
            updates['ignore_reason'] = item.ignore_reason

        if updates:
            # 更新段落
            updated_paragraph = await paragraph_service.update_paragraph(
                paragraph_id=item.id,
                chapter_id=chapter_id,
                **updates
            )
            updated_paragraphs.append(updated_paragraph)

    # 转换为响应模型
    return [ParagraphResponse.from_dict(p.to_dict()) for p in updated_paragraphs]


@router.delete("/{paragraph_id}", response_model=ParagraphDeleteResponse)
async def delete_paragraph(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        paragraph_id: str
):
    """删除段落及其关联的句子"""
    paragraph_service = ParagraphService(db)

    # 获取段落并验证权限
    paragraph = await paragraph_service.get_paragraph_by_id(paragraph_id)
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_id(paragraph.chapter_id)
    project_service = ProjectService(db)
    await project_service.get_project_by_id(chapter.project_id, current_user.id)

    # 删除段落
    await paragraph_service.delete_paragraph(
        paragraph_id=paragraph_id,
        chapter_id=paragraph.chapter_id
    )

    return ParagraphDeleteResponse(
        success=True,
        message="删除成功",
        paragraph_id=paragraph_id
    )


__all__ = ["router"]
