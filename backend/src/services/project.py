"""
项目管理服务 - 项目业务逻辑处理
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.project import FileProcessingStatus, Project, ProjectStatus
from src.models.user import User
from src.tasks.file_processing import process_uploaded_file
from src.utils.storage import MinIOStorage

logger = get_logger(__name__)


class ProjectServiceError(Exception):
    """项目服务异常"""
    pass


class ProjectService:
    """项目管理服务"""

    def __init__(self, db_session: AsyncSession, storage_client: Optional[MinIOStorage] = None):
        self.db_session = db_session
        self.storage_client = storage_client

    async def create_project(
            self,
            user_id: str,
            title: str,
            description: Optional[str] = None,
            original_filename: Optional[str] = None,
            file_info: Optional[Dict[str, Any]] = None,
            storage_info: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        创建新项目

        Args:
            user_id: 用户ID
            title: 项目标题
            description: 项目描述
            original_filename: 原始文件名
            file_info: 文件信息
            storage_info: 存储信息

        Returns:
            创建的项目
        """
        try:
            # 验证用户存在
            user = await self.db_session.get(User, user_id)
            if not user:
                raise ProjectServiceError(f"用户不存在: {user_id}")

            # 创建项目
            project = Project.create_project(
                db_session=self.db_session,
                user_id=user_id,
                title=title,
                description=description,
                original_filename=original_filename
            )

            # 更新文件信息
            if file_info:
                project.file_size = file_info.get('size')
                project.file_type = file_info.get('file_type')
                project.file_hash = file_info.get('file_hash')
                project.file_processing_status = FileProcessingStatus.UPLOADED.value

            # 更新存储信息
            if storage_info:
                project.minio_bucket = storage_info.get('bucket')
                project.minio_object_key = storage_info.get('object_key')

            await self.db_session.commit()
            await self.db_session.refresh(project)

            logger.info(f"创建项目成功: {project.id}, 用户: {user_id}")
            return project

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"创建项目失败: {e}")
            raise ProjectServiceError(f"创建项目失败: {str(e)}")

    async def get_project_by_id(
            self,
            project_id: str,
            user_id: Optional[str] = None
    ) -> Optional[Project]:
        """
        根据ID获取项目

        Args:
            project_id: 项目ID
            user_id: 用户ID（可选，用于权限检查）

        Returns:
            项目信息
        """
        try:
            query = select(Project).filter(Project.id == project_id, Project.is_deleted == False)

            if user_id:
                query = query.filter(Project.user_id == user_id)

            result = await self.db_session.execute(query)
            project = result.scalar_one_or_none()

            return project

        except Exception as e:
            logger.error(f"获取项目失败: {e}")
            return None

    async def get_user_projects(
            self,
            user_id: str,
            status: Optional[ProjectStatus] = None,
            page: int = 1,
            size: int = 20,
            search: Optional[str] = None,
            sort_by: str = "created_at",
            sort_order: str = "desc"
    ) -> Tuple[List[Project], int]:
        """
        获取用户的项目列表

        Args:
            user_id: 用户ID
            status: 项目状态过滤
            page: 页码
            size: 每页大小
            search: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序顺序

        Returns:
            项目列表和总数
        """
        try:
            # 构建查询
            query = select(Project).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            )

            # 状态过滤
            if status:
                query = query.filter(Project.status == status.value)

            # 搜索过滤
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Project.title.ilike(search_term),
                        Project.description.ilike(search_term),
                        Project.original_filename.ilike(search_term)
                    )
                )

            # 获取总数 - 使用独立的count查询，复用相同的过滤条件
            count_query = select(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            )

            # 应用与主查询相同的过滤条件
            if status:
                count_query = count_query.filter(Project.status == status.value)

            if search:
                search_term = f"%{search}%"
                count_query = count_query.filter(
                    or_(
                        Project.title.ilike(search_term),
                        Project.description.ilike(search_term),
                        Project.original_filename.ilike(search_term)
                    )
                )

            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar()

            # 排序
            if hasattr(Project, sort_by):
                sort_column = getattr(Project, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(sort_column)
            else:
                query = query.order_by(desc(Project.created_at))

            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await self.db_session.execute(query)
            projects = result.scalars().all()

            return list(projects), total

        except Exception as e:
            logger.error(f"获取用户项目失败: {e}")
            raise ProjectServiceError(f"获取用户项目失败: {str(e)}")

    async def update_project(
            self,
            project_id: str,
            user_id: str,
            **updates
    ) -> Optional[Project]:
        """
        更新项目信息

        Args:
            project_id: 项目ID
            user_id: 用户ID
            **updates: 更新字段

        Returns:
            更新后的项目
        """
        try:
            # 获取项目
            project = await self.get_project_by_id(project_id, user_id)
            if not project:
                raise ProjectServiceError(f"项目不存在或无权限: {project_id}")

            # 更新字段
            for field, value in updates.items():
                if hasattr(project, field):
                    setattr(project, field, value)

            await self.db_session.commit()
            await self.db_session.refresh(project)

            logger.info(f"更新项目成功: {project_id}")
            return project

        except ProjectServiceError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"更新项目失败: {e}")
            raise ProjectServiceError(f"更新项目失败: {str(e)}")

    async def update_processing_status(
            self,
            project_id: str,
            status: FileProcessingStatus,
            progress: Optional[float] = None,
            error_message: Optional[str] = None,
            **extra_updates
    ) -> bool:
        """
        更新项目处理状态

        Args:
            project_id: 项目ID
            status: 处理状态
            progress: 处理进度
            error_message: 错误信息
            **extra_updates: 额外更新字段

        Returns:
            是否更新成功
        """
        try:
            project = await self.db_session.get(Project, project_id)
            if not project:
                logger.warning(f"项目不存在: {project_id}")
                return False

            # 更新状态
            project.file_processing_status = status.value

            if progress is not None:
                project.update_processing_progress(progress)

            if error_message:
                project.processing_error = error_message

            # 更新额外字段
            for field, value in extra_updates.items():
                if hasattr(project, field):
                    setattr(project, field, value)

            await self.db_session.commit()
            logger.info(f"更新项目处理状态成功: {project_id} -> {status.value}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"更新项目处理状态失败: {e}")
            return False

    async def delete_project(
            self,
            project_id: str,
            user_id: str,
            permanent: bool = False
    ) -> bool:
        """
        删除项目

        Args:
            project_id: 项目ID
            user_id: 用户ID
            permanent: 是否永久删除

        Returns:
            是否删除成功
        """
        try:
            project = await self.get_project_by_id(project_id, user_id)
            if not project:
                raise ProjectServiceError(f"项目不存在或无权限: {project_id}")

            if permanent:
                # 永久删除：删除存储文件和数据库记录
                if self.storage_client and project.minio_object_key:
                    await self.storage_client.delete_file(project.minio_object_key)

                await self.db_session.delete(project)
                logger.info(f"永久删除项目: {project_id}")
            else:
                # 软删除
                project.soft_delete()
                logger.info(f"软删除项目: {project_id}")

            await self.db_session.commit()
            return True

        except ProjectServiceError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"删除项目失败: {e}")
            raise ProjectServiceError(f"删除项目失败: {str(e)}")

    async def restore_project(self, project_id: str, user_id: str) -> bool:
        """
        恢复已删除的项目

        Args:
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            是否恢复成功
        """
        try:
            # 获取已删除的项目
            query = select(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.is_deleted == True
            )
            result = await self.db_session.execute(query)
            project = result.scalar_one_or_none()

            if not project:
                raise ProjectServiceError(f"已删除项目不存在: {project_id}")

            # 恢复项目
            project.restore()
            await self.db_session.commit()

            logger.info(f"恢复项目成功: {project_id}")
            return True

        except ProjectServiceError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"恢复项目失败: {e}")
            raise ProjectServiceError(f"恢复项目失败: {str(e)}")

    async def get_project_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户项目统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        try:
            # 总项目数
            total_query = select(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            )
            total_result = await self.db_session.execute(total_query)
            total_projects = total_result.scalar()

            # 按状态分组统计
            status_query = select(
                Project.status,
                func.count(Project.id)
            ).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            ).group_by(Project.status)

            status_result = await self.db_session.execute(status_query)
            status_stats = {row[0]: row[1] for row in status_result}

            # 按文件类型统计
            file_type_query = select(
                Project.file_type,
                func.count(Project.id)
            ).filter(
                Project.user_id == user_id,
                Project.is_deleted == False,
                Project.file_type.isnot(None)
            ).group_by(Project.file_type)

            file_type_result = await self.db_session.execute(file_type_query)
            file_type_stats = {row[0]: row[1] for row in file_type_result}

            # 存储使用统计
            storage_query = select(
                func.sum(Project.file_size),
                func.avg(Project.file_size),
                func.count(Project.id)
            ).filter(
                Project.user_id == user_id,
                Project.is_deleted == False,
                Project.file_size.isnot(None)
            )
            storage_result = await self.db_session.execute(storage_query)
            storage_row = storage_result.first()

            return {
                "total_projects": total_projects or 0,
                "status_distribution": status_stats,
                "file_type_distribution": file_type_stats,
                "storage_usage": {
                    "total_size": storage_row[0] or 0,
                    "average_size": storage_row[1] or 0,
                    "file_count": storage_row[2] or 0,
                }
            }

        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return {}

    async def search_projects(
            self,
            user_id: str,
            query: str,
            filters: Optional[Dict[str, Any]] = None,
            page: int = 1,
            size: int = 20
    ) -> Tuple[List[Project], int]:
        """
        搜索项目

        Args:
            user_id: 用户ID
            query: 搜索查询
            filters: 过滤条件
            page: 页码
            size: 每页大小

        Returns:
            搜索结果和总数
        """
        try:
            # 构建基础查询
            base_query = select(Project).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            )

            # 搜索条件
            search_term = f"%{query}%"
            base_query = base_query.filter(
                or_(
                    Project.title.ilike(search_term),
                    Project.description.ilike(search_term),
                    Project.original_filename.ilike(search_term)
                )
            )

            # 应用额外过滤条件
            if filters:
                if 'status' in filters:
                    base_query = base_query.filter(Project.status == filters['status'])
                if 'file_type' in filters:
                    base_query = base_query.filter(Project.file_type == filters['file_type'])
                if 'date_from' in filters:
                    base_query = base_query.filter(Project.created_at >= filters['date_from'])
                if 'date_to' in filters:
                    base_query = base_query.filter(Project.created_at <= filters['date_to'])

            # 获取总数 - 使用独立的count查询，复用相同的过滤条件
            count_query = select(func.count(Project.id)).filter(
                Project.user_id == user_id,
                Project.is_deleted == False
            )

            # 应用搜索条件
            search_term = f"%{query}%"
            count_query = count_query.filter(
                or_(
                    Project.title.ilike(search_term),
                    Project.description.ilike(search_term),
                    Project.original_filename.ilike(search_term)
                )
            )

            # 应用额外过滤条件
            if filters:
                if 'status' in filters:
                    count_query = count_query.filter(Project.status == filters['status'])
                if 'file_type' in filters:
                    count_query = count_query.filter(Project.file_type == filters['file_type'])
                if 'date_from' in filters:
                    count_query = count_query.filter(Project.created_at >= filters['date_from'])
                if 'date_to' in filters:
                    count_query = count_query.filter(Project.created_at <= filters['date_to'])

            total_result = await self.db_session.execute(count_query)
            total = total_result.scalar()

            # 分页和排序
            base_query = base_query.order_by(desc(Project.created_at))
            offset = (page - 1) * size
            base_query = base_query.offset(offset).limit(size)

            result = await self.db_session.execute(base_query)
            projects = result.scalars().all()

            return list(projects), total

        except Exception as e:
            logger.error(f"搜索项目失败: {e}")
            raise ProjectServiceError(f"搜索项目失败: {str(e)}")

    async def start_file_processing(
            self,
            project_id: str,
            user_id: str,
            file_path: Optional[str] = None
    ) -> bool:
        """
        启动文件处理任务

        Args:
            project_id: 项目ID
            user_id: 用户ID
            file_path: 文件路径（可选）

        Returns:
            是否启动成功
        """
        try:
            # 获取项目信息
            project = await self.get_project_by_id(project_id, user_id)
            if not project:
                logger.error(f"项目不存在: {project_id}")
                return False

            # 检查项目状态
            if project.file_processing_status != FileProcessingStatus.UPLOADED:
                logger.warning(f"项目状态不允许处理: {project_id}, 当前状态: {project.file_processing_status}")
                return False

            # 启动异步处理任务
            task = process_uploaded_file.delay(
                project_id=project_id,
                user_id=user_id,
                file_path=file_path
            )

            # 更新项目状态为处理中，并记录任务ID
            await self.update_processing_status(
                project_id=project_id,
                status=FileProcessingStatus.PROCESSING,
                progress=0.0,
                task_id=task.id
            )

            logger.info(f"启动文件处理任务成功: {task.id}, 项目: {project_id}")
            return True

        except Exception as e:
            logger.error(f"启动文件处理任务失败: {project_id}, 错误: {str(e)}")
            # 更新状态为失败
            await self.update_processing_status(
                project_id=project_id,
                status=FileProcessingStatus.FAILED,
                error_message=f"启动处理任务失败: {str(e)}"
            )
            return False

    async def get_processing_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取处理任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            from celery.result import AsyncResult

            result = AsyncResult(task_id, app=process_uploaded_file.app)

            if result.ready():
                if result.successful():
                    return {
                        'task_id': task_id,
                        'status': 'completed',
                        'result': result.result,
                        'traceback': None
                    }
                else:
                    return {
                        'task_id': task_id,
                        'status': 'failed',
                        'result': None,
                        'traceback': result.traceback
                    }
            else:
                return {
                    'task_id': task_id,
                    'status': 'processing',
                    'result': None,
                    'traceback': None
                }

        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id}, 错误: {str(e)}")
            return None


__all__ = [
    "ProjectService",
    "ProjectServiceError",
]
