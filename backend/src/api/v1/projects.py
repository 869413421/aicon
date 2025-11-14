"""
项目管理API - 重构后使用schemas模块中的Pydantic模型
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.project import (ProjectArchiveResponse, ProjectCreate, ProjectDeleteResponse, ProjectListResponse, ProjectResponse, ProjectUpdate)
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.project import ProjectStatus as ModelProjectStatus
from src.models.user import User
from src.services.project import ProjectService

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        project_status: Optional[str] = Query("", description="状态过滤"),
        search: Optional[str] = Query("", description="搜索关键词"),
        sort_by: str = Query("created_at", description="排序字段"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序顺序")
):
    """获取用户的项目列表"""
    project_service = ProjectService(db)

    # 处理过滤参数
    status_filter = None
    if project_status and project_status.strip():
        try:
            status_filter = ModelProjectStatus(project_status.strip())
        except ValueError:
            logger.warning(f"无效的项目状态: {project_status}")

    search_query = None
    if search and search.strip():
        search_query = search.strip()

    projects, total = await project_service.get_owner_projects(
        owner_id=current_user.id,
        status=status_filter,
        page=page,
        size=size,
        search=search_query,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # 转换为响应模型
    project_responses = [ProjectResponse.from_dict(project.to_dict()) for project in projects]
    total_pages = (total + size - 1) // size

    return ProjectListResponse(
        projects=project_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """获取项目详情"""
    project_service = ProjectService(db)
    project = await project_service.get_project_by_id(project_id, current_user.id)
    return ProjectResponse.from_dict(project.to_dict())


@router.post("/", response_model=ProjectResponse)
async def create_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_data: ProjectCreate
):
    """创建新项目（支持文件信息）"""
    project_service = ProjectService(db)
    project = await project_service.create_project(
        owner_id=current_user.id,
        title=project_data.title,
        description=project_data.description,
        file_name=project_data.file_name,
        file_size=project_data.file_size,
        file_type=project_data.file_type,
        file_path=project_data.file_path,
        file_hash=project_data.file_hash
    )

    return ProjectResponse.from_dict(project.to_dict())


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str,
        project_data: ProjectUpdate
):
    """更新项目信息（仅标题和描述）"""
    project_service = ProjectService(db)

    updates = {}
    if project_data.title is not None:
        updates['title'] = project_data.title
    if project_data.description is not None:
        updates['description'] = project_data.description

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供更新字段"
        )

    project = await project_service.update_project(
        project_id=project_id,
        owner_id=current_user.id,
        **updates
    )

    return ProjectResponse.from_dict(project.to_dict())


@router.put("/{project_id}/archive", response_model=ProjectArchiveResponse)
async def archive_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """归档项目（不可逆操作）"""
    project_service = ProjectService(db)

    project = await project_service.archive_project(
        project_id=project_id,
        owner_id=current_user.id
    )

    project_response = ProjectResponse.from_dict(project.to_dict())
    return ProjectArchiveResponse(
        message="项目归档成功",
        project=project_response
    )


@router.delete("/{project_id}", response_model=ProjectDeleteResponse)
async def delete_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """删除项目"""
    project_service = ProjectService(db)
    await project_service.delete_project(
        project_id=project_id,
        owner_id=current_user.id
    )

    return ProjectDeleteResponse(
        success=True,
        message="删除成功",
        project_id=project_id
    )


__all__ = ["router"]
