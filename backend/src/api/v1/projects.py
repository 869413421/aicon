"""
项目管理API - 项目CRUD操作和管理
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.project import ProjectStatus
from src.models.user import User
from src.services.project import ProjectService, ProjectServiceError

logger = get_logger(__name__)

router = APIRouter()


# Pydantic模型用于请求和响应
class ProjectCreate(BaseModel):
    """创建项目请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")
    file_id: Optional[str] = Field(None, description="关联的文件ID")


class ProjectCreateWithFile(BaseModel):
    """通过文件创建项目请求模型"""
    file_id: str = Field(..., description="文件ID")
    title: str = Field(..., min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")


class ProjectUpdate(BaseModel):
    """更新项目请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    is_public: Optional[bool] = Field(None, description="是否公开")


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: str
    title: str
    description: Optional[str]
    status: str
    user_id: str
    original_filename: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    file_processing_status: str
    total_chapters: int
    total_paragraphs: int
    total_sentences: int
    word_count: int
    processing_progress: float
    is_public: bool
    is_deleted: bool
    created_at: str
    updated_at: str
    file_size_mb: Optional[float]
    file_extension: Optional[str]
    is_supported_file_type: bool
    can_be_processed: bool

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
    total_pages: int


class ProjectStatistics(BaseModel):
    """项目统计响应模型"""
    total_projects: int
    status_distribution: Dict[str, int]
    file_type_distribution: Dict[str, int]
    storage_usage: Dict[str, Any]


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
    """
    获取用户的项目列表

    Args:
        current_user: 当前用户
        db: 数据库会话
        page: 页码
        size: 每页大小
        project_status: 状态过滤
        search: 搜索关键词
        sort_by: 排序字段
        sort_order: 排序顺序

    Returns:
        项目列表
    """
    try:
        # 处理空字符串参数
        status_filter = None if not project_status or not project_status.strip() else project_status.strip()
        search_query = None if not search or not search.strip() else search.strip()

        project_service = ProjectService(db)
        projects, total = await project_service.get_user_projects(
            user_id=current_user.id,
            status=status_filter,
            page=page,
            size=size,
            search=search_query,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # 转换为响应模型
        project_responses = [ProjectResponse(**project.to_dict()) for project in projects]
        total_pages = (total + size - 1) // size

        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )

    except ProjectServiceError as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"获取项目列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目列表失败"
        )


@router.get("/search", response_model=ProjectListResponse)
async def search_projects(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        q: str = Query(..., min_length=1, max_length=100, description="搜索查询"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页大小"),
        project_status: Optional[ProjectStatus] = Query(None, description="状态过滤"),
        file_type: Optional[str] = Query(None, description="文件类型过滤")
):
    """
    搜索项目

    Args:
        current_user: 当前用户
        db: 数据库会话
        q: 搜索查询
        page: 页码
        size: 每页大小
        project_status: 状态过滤
        file_type: 文件类型过滤

    Returns:
        搜索结果
    """
    try:
        project_service = ProjectService(db)

        # 构建过滤条件
        filters = {}
        if project_status:
            filters['status'] = project_status.value
        if file_type:
            filters['file_type'] = file_type

        projects, total = await project_service.search_projects(
            user_id=current_user.id,
            query=q,
            filters=filters,
            page=page,
            size=size
        )

        # 转换为响应模型
        project_responses = [ProjectResponse(**project.to_dict()) for project in projects]
        total_pages = (total + size - 1) // size

        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )

    except ProjectServiceError as e:
        logger.error(f"搜索项目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索项目失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"搜索项目异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索项目失败"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """
    获取项目详情

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID

    Returns:
        项目详情
    """
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        return ProjectResponse(**project.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目详情失败"
        )


@router.post("/", response_model=ProjectResponse)
async def create_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_data: ProjectCreate
):
    """
    创建新项目（不包含文件上传）

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_data: 项目数据

    Returns:
        创建的项目
    """
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(
            user_id=current_user.id,
            title=project_data.title,
            description=project_data.description
        )

        return ProjectResponse(**project.to_dict())

    except ProjectServiceError as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"创建项目异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建项目失败"
        )


@router.post("/with-file", response_model=ProjectResponse)
async def create_project_with_file(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_data: ProjectCreateWithFile
):
    """
    通过已上传的文件创建项目

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_data: 包含文件ID的项目数据

    Returns:
        创建的项目
    """
    try:
        # TODO: 实现通过文件ID创建项目的逻辑
        # 1. 验证文件ID存在且属于当前用户
        # 2. 获取文件信息
        # 3. 创建项目记录并关联文件

        logger.info(f"用户 {current_user.id} 请求通过文件 {project_data.file_id} 创建项目")

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="通过文件创建项目功能尚未完全实现"
        )

    except Exception as e:
        logger.error(f"通过文件创建项目异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str,
        project_data: ProjectUpdate
):
    """
    更新项目信息

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID
        project_data: 更新数据

    Returns:
        更新后的项目
    """
    try:
        project_service = ProjectService(db)

        # 构建更新数据
        updates = {}
        if project_data.title is not None:
            updates['title'] = project_data.title
        if project_data.description is not None:
            updates['description'] = project_data.description
        if project_data.status is not None:
            updates['status'] = project_data.status.value
        if project_data.is_public is not None:
            updates['is_public'] = project_data.is_public

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供更新字段"
            )

        project = await project_service.update_project(
            project_id=project_id,
            user_id=current_user.id,
            **updates
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在或无权限"
            )

        return ProjectResponse(**project.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新项目失败"
        )


@router.delete("/{project_id}")
async def delete_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str,
        permanent: bool = Query(False, description="是否永久删除")
):
    """
    删除项目

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID
        permanent: 是否永久删除

    Returns:
        删除结果
    """
    try:
        project_service = ProjectService(db)
        success = await project_service.delete_project(
            project_id=project_id,
            user_id=current_user.id,
            permanent=permanent
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在或无权限"
            )

        return {
            "success": True,
            "message": "永久删除" if permanent else "软删除成功",
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除项目失败"
        )


@router.post("/{project_id}/restore")
async def restore_project(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """
    恢复已删除的项目

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID

    Returns:
        恢复结果
    """
    try:
        project_service = ProjectService(db)
        success = await project_service.restore_project(
            project_id=project_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="已删除的项目不存在或无权限"
            )

        return {
            "success": True,
            "message": "项目恢复成功",
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复项目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="恢复项目失败"
        )


@router.get("/statistics/summary", response_model=ProjectStatistics)
async def get_project_statistics(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    获取用户项目统计信息

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        项目统计信息
    """
    try:
        project_service = ProjectService(db)
        stats = await project_service.get_project_statistics(current_user.id)

        return ProjectStatistics(**stats)

    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目统计失败"
        )


@router.get("/{project_id}/download")
async def download_project_file(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """
    下载项目文件

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID

    Returns:
        文件下载响应
    """
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id, current_user.id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        if not project.minio_object_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="项目没有关联的文件"
            )

        # 获取预签名下载URL
        from src.utils.storage import get_storage_client
        storage_client = await get_storage_client()
        download_url = storage_client.get_presigned_url(project.minio_object_key)

        return {
            "success": True,
            "download_url": download_url,
            "filename": project.original_filename or f"project_{project_id}",
            "expires_in": 3600  # 1小时
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载项目文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="下载项目文件失败"
        )


__all__ = ["router"]
