"""
数据库集成测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_
from datetime import datetime
import asyncio

from src.models.project import Project, ProjectStatus, FileProcessingStatus, SupportedFileType
from src.models.user import User
from src.core.database import Base
from src.services.project import ProjectService


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """数据库集成测试"""

    @pytest.fixture(scope="function")
    async def test_engine(self):
        """创建测试数据库引擎"""
        # 使用SQLite内存数据库进行测试
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True
        )

        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        # 清理
        await engine.dispose()

    @pytest.fixture(scope="function")
    async def test_db_session(self, test_engine):
        """创建测试数据库会话"""
        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            yield session

    @pytest.fixture
    async def test_user(self, test_db_session):
        """创建测试用户"""
        user = User(
            id="test-user-123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.now()
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        return user

    @pytest.fixture
    async def sample_projects(self, test_db_session, test_user):
        """创建示例项目"""
        projects = []

        # 创建不同状态的项目
        project_configs = [
            {
                "title": "活跃项目1",
                "description": "这是一个活跃的项目",
                "status": ProjectStatus.ACTIVE,
                "file_type": SupportedFileType.TXT,
                "file_processing_status": FileProcessingStatus.COMPLETED
            },
            {
                "title": "已完成项目",
                "description": "这个项目已经完成",
                "status": ProjectStatus.COMPLETED,
                "file_type": SupportedFileType.MD,
                "file_processing_status": FileProcessingStatus.COMPLETED
            },
            {
                "title": "归档项目",
                "description": "这个项目已归档",
                "status": ProjectStatus.ARCHIVED,
                "file_type": SupportedFileType.DOCX,
                "file_processing_status": FileProcessingStatus.COMPLETED
            },
            {
                "title": "处理中项目",
                "description": "这个项目正在处理中",
                "status": ProjectStatus.ACTIVE,
                "file_type": SupportedFileType.EPUB,
                "file_processing_status": FileProcessingStatus.PROCESSING
            }
        ]

        for config in project_configs:
            project = Project.create_project(
                db_session=test_db_session,
                user_id=test_user.id,
                title=config["title"],
                description=config["description"],
                original_filename=f"{config['title'].lower()}.txt"
            )
            project.status = config["status"].value
            project.file_type = config["file_type"].value
            project.file_processing_status = config["file_processing_status"].value
            project.file_size = 1024 * (len(projects) + 1)
            project.minio_bucket = "test-bucket"
            project.minio_object_key = f"uploads/{test_user.id}/{config['title'].lower()}.txt"

            test_db_session.add(project)
            projects.append(project)

        await test_db_session.commit()

        for project in projects:
            await test_db_session.refresh(project)

        return projects

    async def test_create_project_with_database(self, test_db_session, test_user):
        """测试在数据库中创建项目"""
        project_service = ProjectService(test_db_session)

        project = await project_service.create_project(
            user_id=test_user.id,
            title="数据库测试项目",
            description="测试数据库项目创建功能",
            original_filename="test-database.txt",
            file_info={
                "size": 2048,
                "file_type": SupportedFileType.TXT.value,
                "file_hash": "test-hash-123"
            },
            storage_info={
                "bucket": "test-bucket",
                "object_key": "uploads/test-user/test-database.txt"
            }
        )

        assert project is not None
        assert project.title == "数据库测试项目"
        assert project.user_id == test_user.id
        assert project.file_size == 2048
        assert project.file_type == SupportedFileType.TXT.value
        assert project.minio_bucket == "test-bucket"

        # 验证项目确实保存在数据库中
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        saved_project = result.scalar_one_or_none()

        assert saved_project is not None
        assert saved_project.title == project.title

    async def test_get_user_projects_from_database(self, test_db_session, test_user, sample_projects):
        """测试从数据库获取用户项目"""
        project_service = ProjectService(test_db_session)

        # 获取所有项目
        projects, total = await project_service.get_user_projects(
            user_id=test_user.id,
            page=1,
            size=10
        )

        assert len(projects) == 4
        assert total == 4
        assert all(p.user_id == test_user.id for p in projects)

        # 按状态过滤
        active_projects, active_total = await project_service.get_user_projects(
            user_id=test_user.id,
            status=ProjectStatus.ACTIVE,
            page=1,
            size=10
        )

        assert len(active_projects) == 2
        assert active_total == 2
        assert all(p.status == ProjectStatus.ACTIVE.value for p in active_projects)

        # 搜索过滤
        search_projects, search_total = await project_service.get_user_projects(
            user_id=test_user.id,
            search="活跃",
            page=1,
            size=10
        )

        assert len(search_projects) >= 1
        assert search_total >= 1
        assert all("活跃" in p.title or "活跃" in p.description for p in search_projects)

    async def test_update_project_in_database(self, test_db_session, test_user, sample_projects):
        """测试在数据库中更新项目"""
        project_service = ProjectService(test_db_session)
        project = sample_projects[0]

        updated_project = await project_service.update_project(
            project_id=project.id,
            user_id=test_user.id,
            title="更新后的项目标题",
            description="更新后的项目描述",
            status=ProjectStatus.COMPLETED.value
        )

        assert updated_project.title == "更新后的项目标题"
        assert updated_project.description == "更新后的项目描述"
        assert updated_project.status == ProjectStatus.COMPLETED.value

        # 验证数据库中的更新
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        db_project = result.scalar_one()

        assert db_project.title == "更新后的项目标题"
        assert db_project.description == "更新后的项目描述"
        assert db_project.status == ProjectStatus.COMPLETED.value

    async def test_soft_delete_project_in_database(self, test_db_session, test_user, sample_projects):
        """测试在数据库中软删除项目"""
        project_service = ProjectService(test_db_session)
        project = sample_projects[0]

        # 软删除
        delete_result = await project_service.delete_project(
            project_id=project.id,
            user_id=test_user.id,
            permanent=False
        )

        assert delete_result is True

        # 验证项目被标记为已删除
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        deleted_project = result.scalar_one()

        assert deleted_project.is_deleted is True
        assert deleted_project.deleted_at is not None

        # 验证在正常查询中不会出现
        projects, total = await project_service.get_user_projects(
            user_id=test_user.id,
            page=1,
            size=10
        )

        assert project not in projects

        # 恢复项目
        restore_result = await project_service.restore_project(
            project_id=project.id,
            user_id=test_user.id
        )

        assert restore_result is True

        # 验证项目被恢复
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        restored_project = result.scalar_one()

        assert restored_project.is_deleted is False
        assert restored_project.deleted_at is None

    async def test_permanent_delete_project_in_database(self, test_db_session, test_user, sample_projects):
        """测试在数据库中永久删除项目"""
        project_service = ProjectService(test_db_session)
        project = sample_projects[1]

        # 永久删除
        delete_result = await project_service.delete_project(
            project_id=project.id,
            user_id=test_user.id,
            permanent=True
        )

        assert delete_result is True

        # 验证项目从数据库中被删除
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        deleted_project = result.scalar_one_or_none()

        assert deleted_project is None

    async def test_update_processing_status_in_database(self, test_db_session, sample_projects):
        """测试在数据库中更新处理状态"""
        project_service = ProjectService(test_db_session)
        project = sample_projects[0]

        # 更新处理状态
        update_result = await project_service.update_processing_status(
            project_id=project.id,
            status=FileProcessingStatus.PROCESSING,
            progress=50.0,
            task_id="task-123"
        )

        assert update_result is True

        # 验证状态更新
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        updated_project = result.scalar_one()

        assert updated_project.file_processing_status == FileProcessingStatus.PROCESSING.value
        assert updated_project.processing_progress == 50.0
        assert updated_project.task_id == "task-123"

        # 更新为完成状态
        await project_service.update_processing_status(
            project_id=project.id,
            status=FileProcessingStatus.COMPLETED,
            progress=100.0
        )

        # 验证最终状态
        stmt = select(Project).filter(Project.id == project.id)
        result = await test_db_session.execute(stmt)
        completed_project = result.scalar_one()

        assert completed_project.file_processing_status == FileProcessingStatus.COMPLETED.value
        assert completed_project.processing_progress == 100.0

    async def test_get_project_statistics_from_database(self, test_db_session, test_user, sample_projects):
        """测试从数据库获取项目统计"""
        project_service = ProjectService(test_db_session)

        statistics = await project_service.get_project_statistics(user_id=test_user.id)

        assert statistics["total_projects"] == 4
        assert "status_distribution" in statistics
        assert "file_type_distribution" in statistics
        assert "storage_usage" in statistics

        # 验证状态分布
        status_dist = statistics["status_distribution"]
        assert status_dist.get(ProjectStatus.ACTIVE.value, 0) == 2
        assert status_dist.get(ProjectStatus.COMPLETED.value, 0) == 1
        assert status_dist.get(ProjectStatus.ARCHIVED.value, 0) == 1

        # 验证文件类型分布
        file_type_dist = statistics["file_type_distribution"]
        assert file_type_dist.get(SupportedFileType.TXT.value, 0) == 1
        assert file_type_dist.get(SupportedFileType.MD.value, 0) == 1
        assert file_type_dist.get(SupportedFileType.DOCX.value, 0) == 1
        assert file_type_dist.get(SupportedFileType.EPUB.value, 0) == 1

        # 验证存储使用
        storage_usage = statistics["storage_usage"]
        assert storage_usage["total_size"] > 0
        assert storage_usage["file_count"] == 4

    async def test_search_projects_in_database(self, test_db_session, test_user, sample_projects):
        """测试在数据库中搜索项目"""
        project_service = ProjectService(test_db_session)

        # 搜索所有包含"项目"的项目
        projects, total = await project_service.search_projects(
            user_id=test_user.id,
            query="项目",
            page=1,
            size=10
        )

        assert len(projects) == 4
        assert total == 4

        # 搜索包含"活跃"的项目
        active_projects, active_total = await project_service.search_projects(
            user_id=test_user.id,
            query="活跃",
            page=1,
            size=10
        )

        assert len(active_projects) >= 1
        assert active_total >= 1

        # 带过滤条件的搜索
        filtered_projects, filtered_total = await project_service.search_projects(
            user_id=test_user.id,
            query="项目",
            filters={
                "status": ProjectStatus.ACTIVE.value,
                "file_type": SupportedFileType.TXT.value
            },
            page=1,
            size=10
        )

        assert len(filtered_projects) >= 1

    async def test_project_model_methods(self, test_db_session, test_user):
        """测试项目模型方法"""
        project = Project.create_project(
            db_session=test_db_session,
            user_id=test_user.id,
            title="模型测试项目",
            description="测试项目模型方法",
            original_filename="model-test.txt"
        )

        # 测试进度更新
        project.update_processing_progress(25.0)
        assert project.processing_progress == 25.0

        project.update_processing_progress(75.5)
        assert project.processing_progress == 75.5

        # 测试软删除
        project.soft_delete()
        assert project.is_deleted is True
        assert project.deleted_at is not None

        # 测试恢复
        project.restore()
        assert project.is_deleted is False
        assert project.deleted_at is None

        # 测试验证方法
        assert project.is_valid_status(ProjectStatus.ACTIVE.value) is True
        assert project.is_valid_status("invalid_status") is False

        assert project.is_valid_file_type(SupportedFileType.TXT.value) is True
        assert project.is_valid_file_type("invalid_type") is False

        assert project.is_valid_processing_status(FileProcessingStatus.UPLOADED.value) is True
        assert project.is_valid_processing_status("invalid_status") is False

    async def test_concurrent_project_operations(self, test_db_session, test_user):
        """测试并发项目操作"""
        project_service = ProjectService(test_db_session)

        # 并发创建多个项目
        async def create_project(index):
            return await project_service.create_project(
                user_id=test_user.id,
                title=f"并发项目{index}",
                description=f"并发创建的项目{index}",
                original_filename=f"concurrent{index}.txt"
            )

        # 创建10个项目
        tasks = [create_project(i) for i in range(10)]
        projects = await asyncio.gather(*tasks)

        # 验证所有项目都创建成功
        assert len(projects) == 10
        assert all(p.title.startswith("并发项目") for p in projects)

        # 并发更新项目
        async def update_project(project, index):
            return await project_service.update_project(
                project_id=project.id,
                user_id=test_user.id,
                title=f"更新项目{index}",
                description=f"并发更新的项目{index}"
            )

        update_tasks = [update_project(p, i) for i, p in enumerate(projects)]
        updated_projects = await asyncio.gather(*update_tasks)

        # 验证所有项目都更新成功
        assert len(updated_projects) == 10
        assert all(p.title.startswith("更新项目") for p in updated_projects if p)

    async def test_database_transaction_rollback(self, test_db_session, test_user):
        """测试数据库事务回滚"""
        project_service = ProjectService(test_db_session)

        # 创建一个项目
        project = await project_service.create_project(
            user_id=test_user.id,
            title="回滚测试项目",
            description="测试事务回滚",
            original_filename="rollback-test.txt"
        )

        project_id = project.id

        # 模拟一个会失败的操作
        try:
            # 开始一个新事务
            async with test_db_session.begin():
                # 更新项目
                await project_service.update_project(
                    project_id=project_id,
                    user_id=test_user.id,
                    title="更新后的标题"
                )

                # 故意抛出异常以触发回滚
                raise Exception("模拟错误")

        except Exception:
            # 事务应该已经回滚
            pass

        # 验证项目的标题没有被更新
        stmt = select(Project).filter(Project.id == project_id)
        result = await test_db_session.execute(stmt)
        rollback_project = result.scalar_one()

        assert rollback_project.title == "回滚测试项目"  # 应该保持原样


if __name__ == '__main__':
    pytest.main([__file__])