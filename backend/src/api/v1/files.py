"""
文件管理API - 处理纯文件上传和管理，遵循单一职责原则
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.services.project import ProjectService
from src.utils.file_handlers import FileHandler, FileProcessingError
from src.utils.storage import get_storage_client

logger = get_logger(__name__)

router = APIRouter()


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str
    original_filename: str
    file_size: int
    file_type: str
    storage_key: str


@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(
        *,
        current_user: User = Depends(get_current_user_required),
        file: UploadFile = File(..., description="上传的文件")
):
    """
    纯文件上传，返回文件ID和信息

    Args:
        current_user: 当前用户
        file: 上传的文件

    Returns:
        文件上传结果和文件信息
    """
    try:
        # 验证文件
        file_type, file_info = await FileHandler.validate_file(file)
        logger.info(f"文件验证成功: {file_info}")

        # 生成唯一的文件ID
        import uuid
        file_id = str(uuid.uuid4())

        # 获取存储客户端
        storage_client = await get_storage_client()

        # 上传到MinIO
        storage_result = await storage_client.upload_file(
            user_id=current_user.id,
            file=file,
            metadata={
                "user_id": current_user.id,
                "file_id": file_id,
                "file_type": file_type.value,
                "original_filename": file.filename,
            }
        )

        logger.info(f"文件上传到存储成功: {storage_result}")

        return {
            "success": True,
            "message": "文件上传成功",
            "data": {
                "file_id": file_id,
                "original_filename": file.filename,
                "file_size": file.size,
                "file_type": file_type.value,
                "storage_key": storage_result["object_key"],
                "file_info": file_info,
                "storage_info": storage_result,
            }
        }

    except FileProcessingError as e:
        logger.error(f"文件处理错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件处理失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"上传文件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文件失败: {str(e)}"
        )


@router.delete("/cleanup/orphaned")
async def cleanup_orphaned_files(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        dry_run: bool = Query(True, description="是否为试运行"),
        older_than_days: int = Query(7, ge=1, description="清理多少天前的孤立文件")
):
    """
    清理孤立文件（没有关联项目的文件）

    Args:
        current_user: 当前用户
        db: 数据库会话
        dry_run: 是否为试运行
        older_than_days: 清理多少天前的文件

    Returns:
        清理结果
    """
    try:
        from datetime import datetime, timedelta, timezone

        storage_client = await get_storage_client()
        project_service = ProjectService(db)

        # 获取用户的所有项目
        projects, _ = await project_service.get_user_projects(
            user_id=current_user.id,
            page=1,
            size=1000  # 获取大量项目以检查关联
        )

        # 收集所有项目关联的文件对象键
        project_object_keys = set()
        for project in projects:
            if project.minio_object_key:
                project_object_keys.add(project.minio_object_key)

        # 获取用户上传目录下的所有文件
        user_prefix = f"uploads/{current_user.id}/"
        all_files = await storage_client.list_files(prefix=user_prefix, limit=1000)

        # 找出孤立文件
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        orphaned_files = []

        for file_info in all_files:
            object_key = file_info['object_key']

            # 跳过项目关联的文件
            if object_key in project_object_keys:
                continue

            # 检查文件时间
            if file_info.get('last_modified'):
                try:
                    file_date = datetime.fromisoformat(file_info['last_modified'].replace('Z', '+00:00'))
                    if file_date >= cutoff_date:
                        continue
                except ValueError:
                    logger.warning(f"无法解析文件时间: {file_info['last_modified']}")

            orphaned_files.append(file_info)

        # 如果不是试运行，执行删除
        deleted_files = []
        if not dry_run:
            for file_info in orphaned_files:
                try:
                    success = await storage_client.delete_file(file_info['object_key'])
                    if success:
                        deleted_files.append(file_info['object_key'])
                except Exception as e:
                    logger.error(f"删除文件失败 {file_info['object_key']}: {e}")

        total_size = sum(f.get('size', 0) for f in orphaned_files)
        deleted_size = sum(f.get('size', 0) for f in orphaned_files if f['object_key'] in deleted_files)

        return {
            "success": True,
            "dry_run": dry_run,
            "found_orphaned_files": len(orphaned_files),
            "deleted_files": len(deleted_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
            "files": [
                {
                    "object_key": f['object_key'],
                    "size": f.get('size'),
                    "size_mb": round(f.get('size', 0) / (1024 * 1024), 2),
                    "last_modified": f.get('last_modified')
                }
                for f in orphaned_files
            ]
        }

    except Exception as e:
        logger.error(f"清理孤立文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理孤立文件失败: {str(e)}"
        )


@router.get("/storage/usage")
async def get_storage_usage(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    获取用户存储使用情况

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        存储使用统计
    """
    try:
        storage_client = await get_storage_client()
        project_service = ProjectService(db)

        # 获取项目统计信息
        stats = await project_service.get_project_statistics(current_user.id)

        # 获取存储文件列表
        user_prefix = f"uploads/{current_user.id}/"
        files = await storage_client.list_files(prefix=user_prefix, limit=1000)

        # 按文件类型统计
        file_type_stats = {}
        total_size = 0

        for file_info in files:
            file_size = file_info.get('size', 0)
            total_size += file_size

            # 从对象键推断文件类型
            object_key = file_info['object_key']
            if '.' in object_key.split('/')[-1]:
                ext = object_key.split('.')[-1].lower()
                if ext in file_type_stats:
                    file_type_stats[ext] += 1
                else:
                    file_type_stats[ext] = 1

        return {
            "success": True,
            "total_files": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "file_type_distribution": file_type_stats,
            "project_stats": stats,
            "quota_limit_gb": 10.0,  # 示例：10GB限制
            "quota_usage_percent": round((total_size / (10 * 1024 * 1024 * 1024)) * 100, 2)
        }

    except Exception as e:
        logger.error(f"获取存储使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取存储使用情况失败: {str(e)}"
        )


@router.get("/list")
async def list_user_files(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        prefix: Optional[str] = Query(None, description="文件前缀过滤"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(50, ge=1, le=200, description="每页大小")
):
    """
    列出用户的文件

    Args:
        current_user: 当前用户
        prefix: 文件前缀过滤
        page: 页码
        size: 每页大小

    Returns:
        文件列表
    """
    try:
        storage_client = await get_storage_client()

        # 构建搜索前缀
        user_prefix = f"uploads/{current_user.id}/"
        search_prefix = user_prefix + (prefix or "")

        # 获取文件列表
        files = await storage_client.list_files(prefix=search_prefix, limit=size * page)

        # 计算总数（简化处理）
        total_files = len(files)

        # 分页处理
        start_index = (page - 1) * size
        end_index = start_index + size
        paginated_files = files[start_index:end_index]

        # 清理文件信息
        cleaned_files = []
        for file_info in paginated_files:
            cleaned_files.append({
                "object_key": file_info['object_key'],
                "filename": file_info['object_key'].split('/')[-1],
                "size": file_info.get('size'),
                "size_mb": round(file_info.get('size', 0) / (1024 * 1024), 2),
                "last_modified": file_info.get('last_modified'),
                "url": file_info.get('url'),
                "is_orphaned": True  # 需要进一步检查是否关联到项目
            })

        # 检查哪些文件是孤立的
        project_service = ProjectService(db)
        projects, _ = await project_service.get_user_projects(
            user_id=current_user.id,
            page=1,
            size=1000
        )

        project_object_keys = set()
        for project in projects:
            if project.minio_object_key:
                project_object_keys.add(project.minio_object_key)

        # 更新孤立状态
        for file_info in cleaned_files:
            file_info['is_orphaned'] = file_info['object_key'] not in project_object_keys

        total_pages = (total_files + size - 1) // size

        return {
            "success": True,
            "files": cleaned_files,
            "total_files": total_files,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "orphaned_count": sum(1 for f in cleaned_files if f['is_orphaned'])
        }

    except Exception as e:
        logger.error(f"列出用户文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出用户文件失败: {str(e)}"
        )


@router.post("/batch-delete")
async def batch_delete_files(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        object_keys: List[str]
):
    """
    批量删除文件

    Args:
        current_user: 当前用户
        db: 数据库会话
        object_keys: 要删除的文件对象键列表

    Returns:
        删除结果
    """
    try:
        if not object_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件对象键列表不能为空"
            )

        if len(object_keys) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="单次批量删除文件数量不能超过100个"
            )

        storage_client = await get_storage_client()
        project_service = ProjectService(db)

        # 检查权限并过滤
        user_prefix = f"uploads/{current_user.id}/"
        valid_keys = []
        protected_keys = []

        for object_key in object_keys:
            # 检查文件是否属于当前用户
            if not object_key.startswith(user_prefix):
                logger.warning(f"用户 {current_user.id} 尝试删除不属于自己的文件: {object_key}")
                continue

            # 检查文件是否关联到项目
            projects, _ = await project_service.get_user_projects(
                user_id=current_user.id,
                page=1,
                size=1000
            )

            is_protected = False
            for project in projects:
                if project.minio_object_key == object_key:
                    is_protected = True
                    protected_keys.append(object_key)
                    break

            if not is_protected:
                valid_keys.append(object_key)

        # 执行删除
        deleted_keys = []
        failed_keys = []

        for object_key in valid_keys:
            try:
                success = await storage_client.delete_file(object_key)
                if success:
                    deleted_keys.append(object_key)
                else:
                    failed_keys.append(object_key)
            except Exception as e:
                logger.error(f"删除文件失败 {object_key}: {e}")
                failed_keys.append(object_key)

        return {
            "success": True,
            "requested_files": len(object_keys),
            "valid_files": len(valid_keys),
            "protected_files": len(protected_keys),
            "deleted_files": len(deleted_keys),
            "failed_files": len(failed_keys),
            "deleted_keys": deleted_keys,
            "failed_keys": failed_keys,
            "protected_keys": protected_keys
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除文件失败: {str(e)}"
        )


@router.get("/integrity/check")
async def check_file_integrity(
        *,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db),
        project_id: Optional[str] = Query(None, description="指定项目ID检查")
):
    """
    检查文件完整性

    Args:
        current_user: 当前用户
        db: 数据库会话
        project_id: 可选的项目ID

    Returns:
        完整性检查结果
    """
    try:
        storage_client = await get_storage_client()
        project_service = ProjectService(db)

        if project_id:
            # 检查单个项目
            project = await project_service.get_project_by_id(project_id, current_user.id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="项目不存在"
                )

            projects = [project]
        else:
            # 检查用户所有项目
            projects, _ = await project_service.get_user_projects(
                user_id=current_user.id,
                page=1,
                size=1000
            )

        results = []
        for project in projects:
            if not project.minio_object_key:
                results.append({
                    "project_id": project.id,
                    "project_title": project.title,
                    "file_exists": False,
                    "file_size_match": None,
                    "file_hash_match": None,
                    "error": "项目没有关联的文件"
                })
                continue

            try:
                # 检查文件是否存在
                file_info = await storage_client.get_file_info(project.minio_object_key)
                file_exists = file_info is not None

                if file_exists:
                    # 检查文件大小是否匹配
                    storage_size = file_info.get('size', 0)
                    project_size = project.file_size or 0
                    size_match = storage_size == project_size

                    # 检查文件哈希是否匹配
                    hash_match = file_info.get('metadata', {}).get('file_hash') == project.file_hash

                    results.append({
                        "project_id": project.id,
                        "project_title": project.title,
                        "file_exists": file_exists,
                        "file_size_match": size_match,
                        "file_hash_match": hash_match,
                        "storage_size": storage_size,
                        "project_size": project_size,
                        "error": None
                    })
                else:
                    results.append({
                        "project_id": project.id,
                        "project_title": project.title,
                        "file_exists": False,
                        "file_size_match": None,
                        "file_hash_match": None,
                        "error": "文件在存储中不存在"
                    })

            except Exception as e:
                results.append({
                    "project_id": project.id,
                    "project_title": project.title,
                    "file_exists": False,
                    "file_size_match": None,
                    "file_hash_match": None,
                    "error": f"检查失败: {str(e)}"
                })

        # 统计结果
        total_checked = len(results)
        files_exist = sum(1 for r in results if r['file_exists'])
        size_mismatch = sum(1 for r in results if r['file_exists'] and not r['file_size_match'])
        hash_mismatch = sum(1 for r in results if r['file_exists'] and not r['file_hash_match'])

        return {
            "success": True,
            "project_id": project_id,
            "total_checked": total_checked,
            "files_exist": files_exist,
            "files_missing": total_checked - files_exist,
            "size_mismatch": size_mismatch,
            "hash_mismatch": hash_mismatch,
            "integrity_score": round(((files_exist - size_mismatch - hash_mismatch) / total_checked * 100) if total_checked > 0 else 0, 2),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件完整性检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件完整性检查失败: {str(e)}"
        )


__all__ = ["router"]
