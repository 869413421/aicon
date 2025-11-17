"""
项目管理API - 重构后使用schemas模块中的Pydantic模型
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.project import (ProjectArchiveResponse, ProjectCreate, ProjectDeleteResponse, ProjectListResponse, ProjectProcessingResponse, ProjectResponse,
                                     ProjectRetryResponse, ProjectStatusResponse, ProjectUpdate)
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


@router.post("/", response_model=ProjectProcessingResponse)
async def create_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_data: ProjectCreate
):
    """创建新项目并启动解析任务"""
    project_service = ProjectService(db)

    # 创建项目
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

    # 检查项目是否可以处理
    if not project.can_be_processed():
        return ProjectProcessingResponse(
            success=False,
            message=f"项目状态不允许处理: {project.status}",
            project=ProjectResponse.from_dict(project.to_dict()),
            processing_status=project.status,
            can_retry=False
        )

    # 投递Celery解析任务
    from src.tasks.file_processing import process_uploaded_file
    task = process_uploaded_file.delay(str(project.id), current_user.id)

    logger.info(f"项目 {project.id} 创建成功，已投递解析任务: {task.id}")

    return ProjectProcessingResponse(
        success=True,
        message="项目创建成功，已开始解析文件",
        project=ProjectResponse.from_dict(project.to_dict()),
        task_id=task.id,
        processing_status="parsing",
        can_retry=False
    )


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


@router.post("/{project_id}/retry", response_model=ProjectRetryResponse)
async def retry_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """重试失败的项目解析任务"""
    project_service = ProjectService(db)

    # 获取项目信息
    project = await project_service.get_project_by_id(project_id, current_user.id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 检查项目状态是否可以重试
    if project.status != "failed":
        return ProjectRetryResponse(
            success=False,
            message=f"项目状态不允许重试: {project.status}",
            processing_status=project.status
        )

    # 投递重试任务
    from src.tasks.file_processing import retry_failed_project
    task = retry_failed_project.delay(project_id, current_user.id)

    logger.info(f"项目 {project_id} 重试任务已投递: {task.id}")

    return ProjectRetryResponse(
        success=True,
        message="重试任务已提交",
        task_id=task.id,
        processing_status="parsing"
    )


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """获取项目的详细状态信息"""
    project_service = ProjectService(db)

    try:
        # 获取项目基本信息
        project = await project_service.get_project_by_id(project_id, current_user.id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        # 获取处理状态详情
        from src.services.project_processing import project_processing_service
        processing_details = await project_processing_service.get_processing_status(project_id)

        # 判断是否可以重试
        can_retry = project.status == "failed"

        # 估算剩余时间（如果正在处理中）
        estimated_time = None
        if project.status == "parsing":
            # 简单的时间估算逻辑
            if project.processing_progress and project.processing_progress > 0:
                total_estimated = 300  # 5分钟估算
                elapsed = (project.processing_progress / 100) * total_estimated
                estimated_time = max(0, total_estimated - elapsed)

        return ProjectStatusResponse(
            project=ProjectResponse.from_dict(project.to_dict()),
            processing_details=processing_details,
            task_info={
                "task_id": f"project-{project_id}",
                "status": "running" if project.status == "parsing" else project.status
            },
            can_retry=can_retry,
            estimated_time=estimated_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目状态失败: {str(e)}"
        )


__all__ = ["router"]
