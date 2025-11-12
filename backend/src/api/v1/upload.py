"""
文件上传API - 处理文档上传和文件管理
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.project import FileProcessingStatus, SupportedFileType
from src.models.user import User
from src.services.project import ProjectService, ProjectServiceError
from src.utils.file_handlers import FileHandler, FileProcessingError, get_file_handler
from src.utils.storage import StorageError, get_storage_client

logger = get_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        title: str = Form(..., description="项目标题"),
        description: Optional[str] = Form(None, description="项目描述"),
        file: UploadFile = File(..., description="上传的文件"),
        auto_process: bool = Form(True, description="是否自动处理文件"),
        db_session: AsyncSession = Depends(get_db)
):
    """
    上传文件并创建项目

    Args:
        current_user: 当前用户
        db: 数据库会话
        title: 项目标题
        description: 项目描述
        file: 上传的文件
        auto_process: 是否自动处理文件
        db_session: 数据库会话

    Returns:
        上传结果和项目信息
    """
    try:
        # 验证文件
        file_type, file_info = await FileHandler.validate_file(file)
        logger.info(f"文件验证成功: {file_info}")

        # 获取存储客户端
        storage_client = await get_storage_client()

        # 上传到MinIO
        storage_result = await storage_client.upload_file(
            user_id=current_user.id,
            file=file,
            metadata={
                "user_id": current_user.id,
                "file_type": file_type.value,
                "original_filename": file.filename,
            }
        )

        logger.info(f"文件上传到存储成功: {storage_result}")

        # 保存临时文件用于后续处理
        temp_file_path, saved_filename = await FileHandler.save_temp_file(file)

        try:
            # 创建项目记录
            project_service = ProjectService(db, storage_client)
            project = await project_service.create_project(
                user_id=current_user.id,
                title=title,
                description=description,
                original_filename=file.filename,
                file_info=file_info,
                storage_info=storage_result
            )

            # 如果启用自动处理，开始处理文件
            if auto_process:
                await process_uploaded_file(db, project.id, temp_file_path, file_type)

            return {
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "project": project.to_dict(),
                    "file_info": file_info,
                    "storage_info": storage_result,
                    "auto_process": auto_process,
                }
            }

        finally:
            # 清理临时文件
            try:
                Path(temp_file_path).unlink()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

    except FileProcessingError as e:
        logger.error(f"文件处理错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件处理失败: {str(e)}"
        )
    except StorageError as e:
        logger.error(f"存储错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件存储失败: {str(e)}"
        )
    except ProjectServiceError as e:
        logger.error(f"项目服务错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"项目创建失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"上传文件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文件失败: {str(e)}"
        )


@router.post("/upload-url", response_model=Dict[str, Any])
async def upload_file_from_url(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        title: str = Form(..., description="项目标题"),
        description: Optional[str] = Form(None, description="项目描述"),
        file_url: str = Form(..., description="文件URL"),
        auto_process: bool = Form(True, description="是否自动处理文件"),
        db_session: AsyncSession = Depends(get_db)
):
    """
    从URL上传文件

    Args:
        current_user: 当前用户
        db: 数据库会话
        title: 项目标题
        description: 项目描述
        file_url: 文件URL
        auto_process: 是否自动处理文件
        db_session: 数据库会话

    Returns:
        上传结果和项目信息
    """
    try:
        # TODO: 实现从URL下载文件的功能
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="URL上传功能尚未实现"
        )

    except Exception as e:
        logger.error(f"从URL上传文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从URL上传文件失败: {str(e)}"
        )


@router.get("/presigned-url", response_model=Dict[str, Any])
async def get_presigned_upload_url(
        *,
        current_user: User = Depends(get_current_user_required),
        filename: str,
        file_type: str,
        expires_in: int = 3600
):
    """
    获取预签名上传URL

    Args:
        current_user: 当前用户
        filename: 文件名
        file_type: 文件类型
        expires_in: 过期时间（秒）

    Returns:
        预签名URL
    """
    try:
        storage_client = await get_storage_client()

        # 生成对象键
        object_key = storage_client.generate_object_key(current_user.id, filename)

        # 获取预签名上传URL
        # 注意：MinIO的put_object不支持预签名，这里返回一个概念性的URL
        # 实际前端需要使用/form-data上传

        return {
            "success": True,
            "data": {
                "object_key": object_key,
                "upload_url": f"/api/v1/upload/form/{object_key}",  # 临时URL
                "expires_in": expires_in,
                "max_file_size": 50 * 1024 * 1024,  # 50MB
                "allowed_types": ["txt", "md", "docx", "epub"],
            }
        }

    except Exception as e:
        logger.error(f"获取预签名URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预签名URL失败: {str(e)}"
        )


@router.delete("/file/{object_key}", response_model=Dict[str, Any])
async def delete_file(
        *,
        current_user: User = Depends(get_current_user_required),
        object_key: str,
        db: AsyncSession = Depends(get_db)
):
    """
    删除文件

    Args:
        current_user: 当前用户
        object_key: 文件对象键
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        storage_client = await get_storage_client()

        # 检查文件是否属于当前用户
        if not object_key.startswith(f"uploads/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限删除此文件"
            )

        # 删除文件
        success = await storage_client.delete_file(object_key)

        return {
            "success": success,
            "message": "文件删除成功" if success else "文件删除失败"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}"
        )


@router.get("/file-info/{object_key}", response_model=Dict[str, Any])
async def get_file_info(
        *,
        current_user: User = Depends(get_current_user_required),
        object_key: str
):
    """
    获取文件信息

    Args:
        current_user: 当前用户
        object_key: 文件对象键

    Returns:
        文件信息
    """
    try:
        storage_client = await get_storage_client()

        # 检查文件是否属于当前用户
        if not object_key.startswith(f"uploads/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文件"
            )

        file_info = await storage_client.get_file_info(object_key)

        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )

        return {
            "success": True,
            "data": file_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件信息失败: {str(e)}"
        )


async def process_uploaded_file(
        db: AsyncSession,
        project_id: str,
        file_path: str,
        file_type: SupportedFileType
) -> None:
    """
    处理上传的文件

    Args:
        db: 数据库会话
        project_id: 项目ID
        file_path: 文件路径
        file_type: 文件类型
    """
    try:
        # 更新处理状态为处理中
        project_service = ProjectService(db)
        await project_service.update_processing_status(
            project_id=project_id,
            status=FileProcessingStatus.PROCESSING,
            progress=10.0
        )

        # 获取对应的文件处理器
        handler = get_file_handler(file_type)

        # 读取文件内容
        if file_type == SupportedFileType.TXT:
            content = await handler.read_text_file(file_path)
        elif file_type == SupportedFileType.MD:
            content = await handler.read_markdown_file(file_path)
        elif file_type == SupportedFileType.DOCX:
            content = await handler.read_docx_file(file_path)
        elif file_type == SupportedFileType.EPUB:
            content = await handler.read_epub_file(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        # 统计信息
        word_count = handler.count_words(content) if hasattr(handler, 'count_words') else 0
        paragraph_count = handler.estimate_paragraphs(content) if hasattr(handler, 'estimate_paragraphs') else 0

        # 更新项目信息
        updates = {
            "word_count": word_count,
            "total_paragraphs": paragraph_count,
        }

        # 对于Markdown文件，提取章节信息
        if file_type == SupportedFileType.MD and hasattr(handler, 'extract_metadata'):
            metadata = handler.extract_metadata(content)
            updates["total_chapters"] = metadata.get("chapter_count", 0)

        await project_service.update_project(project_id, **updates)

        # 更新处理状态为完成
        await project_service.update_processing_status(
            project_id=project_id,
            status=FileProcessingStatus.COMPLETED,
            progress=100.0
        )

        logger.info(f"文件处理完成: 项目 {project_id}")

    except Exception as e:
        logger.error(f"处理文件失败: {e}")
        # 更新处理状态为失败
        await project_service.update_processing_status(
            project_id=project_id,
            status=FileProcessingStatus.FAILED,
            error_message=str(e)
        )


@router.post("/process/{project_id}", response_model=Dict[str, Any])
async def process_project_file(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: str
):
    """
    重新处理项目文件

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 项目ID

    Returns:
        处理结果
    """
    try:
        # 获取项目信息
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

        # 从存储下载文件
        storage_client = await get_storage_client()
        file_content = await storage_client.download_file(project.minio_object_key)

        # 保存为临时文件
        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(project.original_filename).suffix
        ) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # 获取文件类型
            file_type = SupportedFileType(project.file_type) if project.file_type else None
            if not file_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法确定文件类型"
                )

            # 处理文件
            await process_uploaded_file(db, project_id, temp_file_path, file_type)

            return {
                "success": True,
                "message": "文件处理已开始",
                "project_id": project_id
            }

        finally:
            # 清理临时文件
            try:
                Path(temp_file_path).unlink()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理项目文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理项目文件失败: {str(e)}"
        )


__all__ = ["router"]
