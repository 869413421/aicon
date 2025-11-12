"""
项目管理API端点单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from src.api.projects import router
from src.core.auth0_auth import get_current_user
from src.core.database import get_db
from src.models.user import User
from src.models.project import Project, ProjectStatus, SupportedFileType


class TestProjectsAPI:
    """项目管理API测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Mock依赖注入
        app.dependency_overrides[get_current_user] = lambda: User(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        return TestClient(app)

    @pytest.fixture
    def mock_project(self):
        """模拟项目"""
        project = Mock(spec=Project)
        project.id = "project-123"
        project.title = "Test Project"
        project.description = "Test description"
        project.status = ProjectStatus.ACTIVE.value
        project.file_type = SupportedFileType.TXT.value
        project.file_size = 1024
        project.original_filename = "test.txt"
        project.created_at = datetime.now()
        project.updated_at = datetime.now()
        project.file_processing_status = "completed"
        project.processing_progress = 100.0
        return project

    @patch('src.api.projects.get_project_service')
    def test_get_projects_success(self, mock_get_service, client):
        """测试获取项目列表成功"""
        # Mock项目服务
        mock_service = AsyncMock()
        mock_service.get_user_projects.return_value = [
            Mock(
                id="project-1",
                title="Project 1",
                status=ProjectStatus.ACTIVE.value,
                file_type=SupportedFileType.TXT.value
            ),
            Mock(
                id="project-2",
                title="Project 2",
                status=ProjectStatus.COMPLETED.value,
                file_type=SupportedFileType.MD.value
            )
        ]
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["projects"]) == 2
        assert data["total"] == 2

        # 验证调用参数
        mock_service.get_user_projects.assert_called_once()

    @patch('src.api.projects.get_project_service')
    def test_get_projects_with_filters(self, mock_get_service, client):
        """测试带过滤条件获取项目列表"""
        mock_service = AsyncMock()
        mock_service.get_user_projects.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/projects",
            params={
                "status": ProjectStatus.ACTIVE.value,
                "page": 2,
                "size": 10,
                "search": "test",
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )
        assert response.status_code == 200

        # 验证调用参数
        call_args = mock_service.get_user_projects.call_args
        assert call_args.kwargs["status"] == ProjectStatus.ACTIVE
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["size"] == 10
        assert call_args.kwargs["search"] == "test"
        assert call_args.kwargs["sort_by"] == "created_at"
        assert call_args.kwargs["sort_order"] == "desc"

    @patch('src.api.projects.get_project_service')
    def test_get_projects_service_error(self, mock_get_service, client):
        """测试获取项目列表服务错误"""
        mock_service = AsyncMock()
        mock_service.get_user_projects.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "服务错误" in data["message"]

    @patch('src.api.projects.get_project_service')
    def test_get_project_by_id_success(self, mock_get_service, client, mock_project):
        """测试根据ID获取项目成功"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects/project-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project"]["id"] == "project-123"
        assert data["project"]["title"] == "Test Project"

    @patch('src.api.projects.get_project_service')
    def test_get_project_by_id_not_found(self, mock_get_service, client):
        """测试根据ID获取项目不存在"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "项目不存在" in data["message"]

    @patch('src.api.projects.get_project_service')
    def test_create_project_success(self, mock_get_service, client, mock_project):
        """测试创建项目成功"""
        mock_service = AsyncMock()
        mock_service.create_project.return_value = mock_project
        mock_get_service.return_value = mock_service

        request_data = {
            "title": "New Project",
            "description": "New project description"
        }

        response = client.post("/api/v1/projects", json=request_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["project"]["id"] == "project-123"
        assert data["project"]["title"] == "New Project"

        # 验证调用参数
        mock_service.create_project.assert_called_once_with(
            user_id="test-user-id",
            title="New Project",
            description="New project description",
            original_filename=None,
            file_info=None,
            storage_info=None
        )

    @patch('src.api.projects.get_project_service')
    def test_create_project_invalid_data(self, mock_get_service, client):
        """测试创建项目数据无效"""
        response = client.post("/api/v1/projects", json={})
        assert response.status_code == 422

    @patch('src.api.projects.get_project_service')
    def test_create_project_service_error(self, mock_get_service, client):
        """测试创建项目服务错误"""
        mock_service = AsyncMock()
        mock_service.create_project.side_effect = Exception("Creation failed")
        mock_get_service.return_value = mock_service

        request_data = {
            "title": "New Project"
        }

        response = client.post("/api/v1/projects", json=request_data)
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('src.api.projects.get_project_service')
    def test_update_project_success(self, mock_get_service, client, mock_project):
        """测试更新项目成功"""
        mock_service = AsyncMock()
        mock_service.update_project.return_value = mock_project
        mock_get_service.return_value = mock_service

        update_data = {
            "title": "Updated Project",
            "description": "Updated description"
        }

        response = client.put("/api/v1/projects/project-123", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project"]["title"] == "Updated Project"

        # 验证调用参数
        mock_service.update_project.assert_called_once_with(
            project_id="project-123",
            user_id="test-user-id",
            title="Updated Project",
            description="Updated description"
        )

    @patch('src.api.projects.get_project_service')
    def test_update_project_not_found(self, mock_get_service, client):
        """测试更新项目不存在"""
        mock_service = AsyncMock()
        mock_service.update_project.side_effect = Exception("Project not found")
        mock_get_service.return_value = mock_service

        update_data = {
            "title": "Updated Project"
        }

        response = client.put("/api/v1/projects/nonexistent", json=update_data)
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('src.api.projects.get_project_service')
    def test_delete_project_success(self, mock_get_service, client):
        """测试删除项目成功"""
        mock_service = AsyncMock()
        mock_service.delete_project.return_value = True
        mock_get_service.return_value = mock_service

        response = client.delete("/api/v1/projects/project-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "项目删除成功"

        # 验证调用参数
        mock_service.delete_project.assert_called_once_with(
            project_id="project-123",
            user_id="test-user-id",
            permanent=False
        )

    @patch('src.api.projects.get_project_service')
    def test_delete_project_permanent(self, mock_get_service, client):
        """测试永久删除项目"""
        mock_service = AsyncMock()
        mock_service.delete_project.return_value = True
        mock_get_service.return_value = mock_service

        response = client.delete("/api/v1/projects/project-123?permanent=true")
        assert response.status_code == 200

        # 验证调用参数
        mock_service.delete_project.assert_called_once_with(
            project_id="project-123",
            user_id="test-user-id",
            permanent=True
        )

    @patch('src.api.projects.get_project_service')
    def test_delete_project_not_found(self, mock_get_service, client):
        """测试删除项目不存在"""
        mock_service = AsyncMock()
        mock_service.delete_project.side_effect = Exception("Project not found")
        mock_get_service.return_value = mock_service

        response = client.delete("/api/v1/projects/nonexistent")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('src.api.projects.get_project_service')
    def test_restore_project_success(self, mock_get_service, client):
        """测试恢复项目成功"""
        mock_service = AsyncMock()
        mock_service.restore_project.return_value = True
        mock_get_service.return_value = mock_service

        response = client.post("/api/v1/projects/project-123/restore")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "项目恢复成功"

        # 验证调用参数
        mock_service.restore_project.assert_called_once_with(
            project_id="project-123",
            user_id="test-user-id"
        )

    @patch('src.api.projects.get_project_service')
    def test_get_project_statistics_success(self, mock_get_service, client):
        """测试获取项目统计成功"""
        mock_service = AsyncMock()
        mock_service.get_project_statistics.return_value = {
            "total_projects": 10,
            "status_distribution": {
                "active": 5,
                "completed": 3,
                "archived": 2
            },
            "file_type_distribution": {
                "txt": 6,
                "md": 3,
                "docx": 1
            },
            "storage_usage": {
                "total_size": 1048576,
                "average_size": 104857,
                "file_count": 10
            }
        }
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["statistics"]["total_projects"] == 10
        assert "status_distribution" in data["statistics"]
        assert "file_type_distribution" in data["statistics"]
        assert "storage_usage" in data["statistics"]

    @patch('src.api.projects.get_project_service')
    def test_search_projects_success(self, mock_get_service, client):
        """测试搜索项目成功"""
        mock_service = AsyncMock()
        mock_service.search_projects.return_value = ([], 0)
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/projects/search",
            params={"q": "test project", "page": 1, "size": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "projects" in data
        assert "total" in data

        # 验证调用参数
        mock_service.search_projects.assert_called_once_with(
            user_id="test-user-id",
            query="test project",
            filters=None,
            page=1,
            size=20
        )

    @patch('src.api.projects.get_project_service')
    def test_search_projects_with_filters(self, mock_get_service, client):
        """测试带过滤条件的搜索项目"""
        mock_service = AsyncMock()
        mock_service.search_projects.return_value = ([], 0)
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/projects/search",
            params={
                "q": "test",
                "status": ProjectStatus.ACTIVE.value,
                "file_type": SupportedFileType.TXT.value,
                "page": 1,
                "size": 10
            }
        )
        assert response.status_code == 200

        # 验证调用参数
        call_args = mock_service.search_projects.call_args
        assert call_args.kwargs["query"] == "test"
        assert "filters" in call_args.kwargs
        assert call_args.kwargs["filters"]["status"] == ProjectStatus.ACTIVE.value
        assert call_args.kwargs["filters"]["file_type"] == SupportedFileType.TXT.value

    def test_search_projects_no_query(self, client):
        """测试搜索项目未提供查询"""
        response = client.get("/api/v1/projects/search")
        assert response.status_code == 422

    @patch('src.api.projects.get_project_service')
    def test_start_processing_success(self, mock_get_service, client):
        """测试启动文件处理成功"""
        mock_service = AsyncMock()
        mock_service.start_file_processing.return_value = True
        mock_get_service.return_value = mock_service

        response = client.post("/api/v1/projects/project-123/process")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "文件处理已启动"

        # 验证调用参数
        mock_service.start_file_processing.assert_called_once_with(
            project_id="project-123",
            user_id="test-user-id",
            file_path=None
        )

    @patch('src.api.projects.get_project_service')
    def test_start_processing_not_found(self, mock_get_service, client):
        """测试启动处理项目不存在"""
        mock_service = AsyncMock()
        mock_service.start_file_processing.return_value = False
        mock_get_service.return_value = mock_service

        response = client.post("/api/v1/projects/nonexistent/process")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "启动处理失败" in data["message"]

    @patch('src.api.projects.get_project_service')
    def test_get_processing_status_success(self, mock_get_service, client):
        """测试获取处理状态成功"""
        mock_service = AsyncMock()
        mock_service.get_processing_task_status.return_value = {
            "task_id": "task-123",
            "status": "completed",
            "result": {"processed": True},
            "traceback": None
        }
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/projects/project-123/processing-status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["task_status"]["status"] == "completed"

    @patch('src.api.projects.get_project_service')
    def test_get_processing_status_no_task_id(self, mock_get_service, client, mock_project):
        """测试获取处理状态项目无任务ID"""
        mock_service = AsyncMock()
        mock_service.get_project_by_id.return_value = mock_project
        mock_service.get_processing_task_status.return_value = None
        mock_get_service.return_value = mock_service

        # Mock project without task_id
        mock_project.task_id = None

        response = client.get("/api/v1/projects/project-123/processing-status")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "没有正在进行的处理任务" in data["message"]


class TestProjectsAPIIntegration:
    """项目管理API集成测试"""

    @patch('src.api.projects.get_project_service')
    def test_project_crud_workflow(self, mock_get_service):
        """测试项目CRUD完整工作流程"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Mock依赖
        app.dependency_overrides[get_current_user] = lambda: User(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        client = TestClient(app)

        # Mock项目服务
        mock_service = AsyncMock()
        mock_project = Mock()
        mock_project.id = "project-123"
        mock_project.title = "Test Project"
        mock_project.description = "Test description"
        mock_project.status = ProjectStatus.ACTIVE.value

        # 配置mock返回值
        mock_service.create_project.return_value = mock_project
        mock_service.get_project_by_id.return_value = mock_project
        mock_service.update_project.return_value = mock_project
        mock_service.delete_project.return_value = True
        mock_service.get_user_projects.return_value = [mock_project]

        mock_get_service.return_value = mock_service

        # 1. 创建项目
        create_response = client.post(
            "/api/v1/projects",
            json={"title": "Test Project", "description": "Test description"}
        )
        assert create_response.status_code == 201
        create_data = create_response.json()
        assert create_data["success"] is True

        # 2. 获取项目
        get_response = client.get("/api/v1/projects/project-123")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True

        # 3. 更新项目
        update_response = client.put(
            "/api/v1/projects/project-123",
            json={"title": "Updated Project"}
        )
        assert update_response.status_code == 200

        # 4. 列出项目
        list_response = client.get("/api/v1/projects")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert len(list_data["projects"]) == 1

        # 5. 删除项目
        delete_response = client.delete("/api/v1/projects/project-123")
        assert delete_response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__])