"""
项目管理服务单元测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.project import Project, ProjectStatus, FileProcessingStatus, SupportedFileType
from src.models.user import User
from src.services.project import ProjectService, ProjectServiceError
from src.utils.storage import MinIOStorage, StorageError


class TestProjectService:
    """ProjectService测试"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_storage_client(self):
        """模拟存储客户端"""
        return AsyncMock(spec=MinIOStorage)

    @pytest.fixture
    def project_service(self, mock_db_session, mock_storage_client):
        """创建项目服务实例"""
        return ProjectService(mock_db_session, mock_storage_client)

    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        user = User(
            id="user123",
            email="test@example.com",
            username="testuser",
            created_at=datetime.now()
        )
        return user

    @pytest.fixture
    def mock_project(self, mock_user):
        """模拟项目"""
        project = Project(
            id="project123",
            user_id=mock_user.id,
            title="Test Project",
            description="Test Description",
            status=ProjectStatus.DRAFT,
            file_processing_status=FileProcessingStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return project

    async def test_create_project_success(self, project_service, mock_db_session, mock_user):
        """测试创建项目成功"""
        # Mock用户查询
        mock_db_session.get.return_value = mock_user

        # Mock Project.create_project
        with patch('src.models.project.Project.create_project') as mock_create:
            mock_project = Project(
                id="project123",
                user_id=mock_user.id,
                title="Test Project",
                description="Test Description",
                status=ProjectStatus.DRAFT,
                file_processing_status=FileProcessingStatus.PENDING
            )
            mock_create.return_value = mock_project

            # Mock commit
            mock_db_session.commit = AsyncMock()
            mock_db_session.refresh = AsyncMock()

            result = await project_service.create_project(
                user_id=mock_user.id,
                title="Test Project",
                description="Test Description"
            )

            assert result.id == "project123"
            assert result.user_id == mock_user.id
            assert result.title == "Test Project"
            assert result.description == "Test Description"

            mock_db_session.get.assert_called_once_with(User, mock_user.id)
            mock_create.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(result)

    async def test_create_project_user_not_found(self, project_service, mock_db_session):
        """测试创建项目用户不存在"""
        mock_db_session.get.return_value = None

        with pytest.raises(ProjectServiceError):
            await project_service.create_project(
                user_id="nonexistent",
                title="Test Project"
            )

    async def test_create_project_with_file_info(self, project_service, mock_db_session, mock_user):
        """测试创建项目包含文件信息"""
        mock_db_session.get.return_value = mock_user
        file_info = {
            'size': 1024,
            'file_type': SupportedFileType.TXT,
            'file_hash': 'test-hash'
        }

        with patch('src.models.project.Project.create_project') as mock_create:
            mock_project = Project(
                id="project123",
                user_id=mock_user.id,
                title="Test Project"
            )
            mock_create.return_value = mock_project

            mock_db_session.commit = AsyncMock()
            mock_db_session.refresh = AsyncMock()

            result = await project_service.create_project(
                user_id=mock_user.id,
                title="Test Project",
                file_info=file_info
            )

            assert result.file_size == 1024
            assert result.file_type == SupportedFileType.TXT
            assert result.file_hash == 'test-hash'

    async def test_get_project_by_id_success(self, project_service, mock_db_session, mock_project):
        """测试根据ID获取项目成功"""
        # Mock查询结果
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_db_session.execute.return_value = mock_result

        result = await project_service.get_project_by_id("project123", mock_project.user_id)

        assert result == mock_project

        # 验证查询条件
        call_args = mock_db_session.execute.call_args
        query = call_args[0][0]
        assert str(query) == str(select(Project).filter(Project.id == 'project123', Project.is_deleted == False, Project.user_id == 'user123'))

    async def test_get_project_by_id_not_found(self, project_service, mock_db_session):
        """测试根据ID获取项目（不存在）"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await project_service.get_project_by_id("nonexistent", "user123")

        assert result is None

    async def test_get_project_by_id_no_user_check(self, project_service, mock_db_session, mock_project):
        """测试根据ID获取项目（不检查用户权限）"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_db_session.execute.return_value = mock_result

        result = await project_service.get_project_by_id("project123")

        assert result == mock_project

        # 验证查询条件（不包含用户过滤）
        call_args = mock_db_session.execute.call_args
        query = call_args[0][0]
        assert str(query) == str(select(Project).filter(Project.id == 'project123', Project.is_deleted == False))

    async def test_get_user_projects_success(self, project_service, mock_db_session, mock_project):
        """测试获取用户项目列表成功"""
        mock_projects = [mock_project]
        mock_total = 1

        # Mock总数查询
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = mock_total
        mock_db_session.execute.return_value = mock_count_result

        # Mock项目查询
        mock_project_result = Mock()
        mock_project_result.scalars.return_value.all.return_value = mock_projects
        mock_db_session.execute.return_value = mock_project_result

        projects, total = await project_service.get_user_projects(
            user_id=mock_project.user_id,
            page=1,
            size=20
        )

        assert len(projects) == 1
        assert total == 1
        assert projects[0] == mock_project

    async def test_get_user_projects_with_filters(self, project_service, mock_db_session, mock_project):
        """测试获取用户项目列表（带过滤条件）"""
        mock_projects = [mock_project]
        mock_total = 1

        # Mock总数查询
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = mock_total
        mock_db_session.execute.return_value = mock_count_result

        # Mock项目查询
        mock_project_result = Mock()
        mock_project_result.scalars.return_value.all.return_value = mock_projects
        mock_db_session.execute.return_value = mock_project_result

        projects, total = await project_service.get_user_projects(
            user_id=mock_project.user_id,
            status=ProjectStatus.DRAFT,
            search="Test",
            sort_by="title",
            sort_order="asc"
        )

        assert len(projects) == 1
        assert total == 1

    async def test_update_project_success(self, project_service, mock_db_session, mock_project):
        """测试更新项目成功"""
        mock_db_session.get.return_value = mock_project
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        updates = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'status': ProjectStatus.COMPLETED
        }

        result = await project_service.update_project(
            project_id=mock_project.id,
            user_id=mock_project.user_id,
            **updates
        )

        assert result.title == 'Updated Title'
        assert result.description == 'Updated Description'
        assert result.status == ProjectStatus.COMPLETED

        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(result)

    async def test_update_project_not_found(self, project_service, mock_db_session):
        """测试更新项目（项目不存在）"""
        mock_db_session.get.return_value = None

        with pytest.raises(ProjectServiceError):
            await project_service.update_project(
                project_id="nonexistent",
                user_id="user123",
                title="Updated Title"
            )

    async def test_delete_project_soft(self, project_service, mock_db_session, mock_project, mock_storage_client):
        """测试软删除项目"""
        mock_db_session.get.return_value = mock_project
        mock_db_session.commit = AsyncMock()

        result = await project_service.delete_project(
            project_id=mock_project.id,
            user_id=mock_project.user_id,
            permanent=False
        )

        assert result is True
        assert mock_project.is_deleted is True
        mock_db_session.commit.assert_called_once()
        mock_storage_client.delete_file.assert_not_called()

    async def test_delete_project_permanent(self, project_service, mock_db_session, mock_project, mock_storage_client):
        """测试永久删除项目"""
        mock_db_session.get.return_value = mock_project
        mock_storage_client.delete_file = AsyncMock(return_value=True)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()

        result = await project_service.delete_project(
            project_id=mock_project.id,
            user_id=mock_project.user_id,
            permanent=True
        )

        assert result is True
        mock_storage_client.delete_file.assert_called_once()
        mock_db_session.delete.assert_called_once_with(mock_project)
        mock_db_session.commit.assert_called_once()

    async def test_restore_project_success(self, project_service, mock_db_session, mock_project):
        """测试恢复项目成功"""
        # 设置项目为已删除状态
        mock_project.is_deleted = True

        # Mock查询已删除的项目
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_db_session.execute.return_value = mock_result

        mock_db_session.commit = AsyncMock()

        result = await project_service.restore_project(
            project_id=mock_project.id,
            user_id=mock_project.user_id
        )

        assert result is True
        assert mock_project.is_deleted is False
        mock_db_session.commit.assert_called_once()

    async def test_restore_project_not_found(self, project_service, mock_db_session):
        """测试恢复项目（项目不存在）"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ProjectServiceError):
            await project_service.restore_project(
                project_id="nonexistent",
                user_id="user123"
            )

    async def test_update_processing_status(self, project_service, mock_db_session, mock_project):
        """测试更新处理状态"""
        mock_db_session.get.return_value = mock_project
        mock_db_session.commit = AsyncMock()

        result = await project_service.update_processing_status(
            project_id=mock_project.id,
            status=FileProcessingStatus.PROCESSING,
            progress=50.0,
            error_message="Processing error"
        )

        assert result is True
        assert mock_project.file_processing_status == FileProcessingStatus.PROCESSING.value
        assert mock_project.processing_progress == 50.0
        assert mock_project.processing_error == "Processing error"
        mock_db_session.commit.assert_called_once()

    async def test_update_processing_status_project_not_found(self, project_service, mock_db_session):
        """测试更新处理状态（项目不存在）"""
        mock_db_session.get.return_value = None

        result = await project_service.update_processing_status(
            project_id="nonexistent",
            status=FileProcessingStatus.PROCESSING
        )

        assert result is False

    async def test_get_project_statistics(self, project_service, mock_db_session, mock_project):
        """测试获取项目统计信息"""
        # Mock查询
        total_query_result = Mock()
        total_query_result.scalar.return_value = 5
        status_query_result = Mock()
        status_query_result.all.return_value = [
            (ProjectStatus.DRAFT, 2),
            (ProjectStatus.COMPLETED, 2),
            (ProjectStatus.PROCESSING, 1)
        ]
        file_type_query_result = Mock()
        file_type_query_result.all.return_value = [
            (SupportedFileType.TXT, 2),
            (SupportedFileType.MD, 2),
            (SupportedFileType.DOCX, 1)
        ]
        storage_query_result = Mock()
        storage_query_result.first.return_value = (10240, 2048, 3)

        mock_db_session.execute.side_effect = [
            total_query_result,
            status_query_result,
            file_type_query_result,
            storage_query_result
        ]

        result = await project_service.get_project_statistics(mock_project.user_id)

        assert result['total_projects'] == 5
        assert result['status_distribution'][ProjectStatus.DRAFT] == 2
        assert result['file_type_distribution'][SupportedFileType.TXT] == 2
        assert result['storage_usage']['total_size'] == 10240
        assert result['storage_usage']['file_count'] == 3

    async def test_search_projects(self, project_service, mock_db_session, mock_project):
        """测试搜索项目"""
        mock_projects = [mock_project]
        mock_total = 1

        # Mock总数查询
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = mock_total
        mock_db_session.execute.return_value = mock_count_result

        # Mock搜索结果查询
        mock_search_result = Mock()
        mock_search_result.scalars.return_value.all.return_value = mock_projects
        mock_db_session.execute.return_value = mock_search_result

        projects, total = await project_service.search_projects(
            user_id=mock_project.user_id,
            query="Test",
            page=1,
            size=20
        )

        assert len(projects) == 1
        assert total == 1

    async def test_start_file_processing_success(self, project_service, mock_db_session, mock_project):
        """测试启动文件处理任务成功"""
        mock_db_session.get.return_value = mock_project
        mock_project.file_processing_status = FileProcessingStatus.UPLOADED

        # Mock任务启动
        with patch('src.tasks.file_processing.process_uploaded_file') as mock_task:
            mock_task_instance = Mock()
            mock_task_instance.delay.return_value = Mock()
            mock_task_instance.delay.return_value.id = "task123"

            mock_db_session.commit = AsyncMock()

            result = await project_service.start_file_processing(
                project_id=mock_project.id,
                user_id=mock_project.user_id
            )

            assert result is True
            mock_task_instance.delay.assert_called_once_with(
                project_id=mock_project.id,
                user_id=mock_project.user_id,
                file_path=None
            )
            mock_db_session.commit.assert_called_once()

    async def test_start_file_processing_invalid_status(self, project_service, mock_db_session, mock_project):
        """测试启动文件处理任务（状态无效）"""
        mock_db_session.get.return_value = mock_project
        mock_project.file_processing_status = FileProcessingStatus.PROCESSING

        result = await project_service.start_file_processing(
            project_id=mock_project.id,
            user_id=mock_project.user_id
        )

        assert result is False

    async def test_start_file_processing_project_not_found(self, project_service, mock_db_session):
        """测试启动文件处理任务（项目不存在）"""
        mock_db_session.get.return_value = None

        result = await project_service.start_file_processing(
            project_id="nonexistent",
            user_id="user123"
        )

        assert result is False

    async def test_get_processing_task_status_completed(self, project_service):
        """测试获取处理任务状态（已完成）"""
        with patch('src.tasks.file_processing.process_uploaded_file.app') as mock_app:
            mock_app.AsyncResult = Mock()
            mock_result = Mock()
            mock_result.ready.return_value = True
            mock_result.successful.return_value = True
            mock_result.result = {'success': True, 'project_id': 'project123'}
            mock_result.traceback = None
            mock_app.AsyncResult.return_value = mock_result

            result = await project_service.get_processing_task_status("task123")

            assert result is not None
            assert result['status'] == 'completed'
            assert result['success'] is True
            assert result['result']['project_id'] == 'project123'

    async def test_get_processing_task_status_failed(self, project_service):
        """测试获取处理任务状态（失败）"""
        with patch('src.tasks.file_processing.process_uploaded_file.app') as mock_app:
            mock_app.AsyncResult = Mock()
            mock_result = Mock()
            mock_result.ready.return_value = True
            mock_result.successful.return_value = False
            mock_result.result = None
            mock_result.traceback = "Error traceback"
            mock_app.AsyncResult.return_value = mock_result

            result = await project_service.get_processing_task_status("task123")

            assert result is not None
            assert result['status'] == 'failed'
            assert result['success'] is False
            assert result['error'] is None
            assert result['traceback'] == "Error traceback"

    async def test_get_processing_task_status_processing(self, project_service):
        """测试获取处理任务状态（处理中）"""
        with patch('src.tasks.file_processing.process_uploaded_file.app') as mock_app:
            mock_app.AsyncResult = Mock()
            mock_result = Mock()
            mock_result.ready.return_value = False
            mock_app.AsyncResult.return_value = mock_result

            result = await project_service.get_processing_task_status("task123")

            assert result is not None
            assert result['status'] == 'processing'
            assert result['result'] is None

    async def test_get_processing_task_status_error(self, project_service):
        """测试获取处理任务状态（错误）"""
        with patch('src.tasks.file_processing.process_uploaded_file.app') as mock_app:
            mock_app.AsyncResult = Mock()
            mock_app.AsyncResult.side_effect = Exception("Task error")

            result = await project_service.get_processing_task_status("task123")

            assert result is None


class TestProjectServiceError:
    """ProjectService异常测试"""

    def test_project_service_error_creation(self):
        """测试ProjectServiceError异常创建"""
        error = ProjectServiceError("Test error")
        assert str(error) == "Test error"

    def test_project_service_error_inheritance(self):
        """测试ProjectServiceError继承关系"""
        error = ProjectServiceError("Test error")
        assert isinstance(error, Exception)


class TestProjectServiceIntegration:
    """ProjectService集成测试"""

    @pytest.mark.asyncio
    async def test_complete_project_workflow(self):
        """测试完整的项目工作流"""
        # 这个测试需要真实的数据库连接，暂时跳过
        pass

    @pytest.mark.asyncio
    async def test_project_with_file_processing(self):
        """测试包含文件处理的项目工作流"""
        # 这个测试需要真实的数据库连接和Celery worker，暂时跳过
        pass


if __name__ == '__main__':
    pytest.main([__file__])