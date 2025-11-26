"""
服务基类 - 提供统一的数据库会话管理和基础功能
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.core.logging import get_logger

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

logger = get_logger(__name__)


class BaseService:
    """
    服务基类

    提供统一的数据库会话管理，避免在服务层手动传递db_session参数。

    特性：
    - 自动管理数据库会话生命周期
    - 提供事务管理方法
    - 统一的日志记录
    - 异常处理和事务回滚
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化服务实例

        Args:
            db_session: 可选的外部数据库会话。如果提供，服务将使用此会话；
                       如果不提供，将创建新的会话（主要用于测试和特殊场景）

        Note:
            在FastAPI应用中，通常通过依赖注入提供db_session
            在后台任务中，可能需要服务自己管理会话
        """
        self._db_session = db_session
        self._should_close_session = db_session is None

    @property
    def db_session(self) -> AsyncSession:
        """
        获取数据库会话

        Returns:
            AsyncSession: 当前可用的数据库会话

        Raises:
            RuntimeError: 如果没有可用的数据库会话
        """
        if self._db_session is None:
            # 创建新会话（主要用于独立使用场景）
            self._db_session = AsyncSessionLocal()
            self._should_close_session = True
            logger.debug(f"{self.__class__.__name__} 创建了新的数据库会话")

        return self._db_session

    async def close_session(self):
        """
        关闭数据库会话

        只有当服务自己创建会话时才会关闭，外部传入的会话由创建者负责关闭。
        """
        if self._should_close_session and self._db_session:
            await self._db_session.close()
            self._db_session = None
            logger.debug(f"{self.__class__.__name__} 关闭了数据库会话")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if exc_type:
            # 如果有异常，回滚事务
            await self.rollback()

        # 关闭会话（如果需要）
        await self.close_session()

    async def commit(self):
        """
        提交当前事务

        Raises:
            Exception: 提交失败时抛出异常
        """
        try:
            await self.db_session.commit()
            logger.debug(f"{self.__class__.__name__} 提交事务成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 提交事务失败: {e}")
            await self.rollback()
            raise

    async def rollback(self):
        """
        回滚当前事务
        """
        try:
            await self.db_session.rollback()
            logger.debug(f"{self.__class__.__name__} 回滚事务成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 回滚事务失败: {e}")

    async def flush(self):
        """
        刷新当前会话，将操作发送到数据库但不提交

        用于获取数据库生成的ID等值
        """
        try:
            await self.db_session.flush()
            logger.debug(f"{self.__class__.__name__} 刷新会话成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 刷新会话失败: {e}")
            await self.rollback()
            raise

    async def refresh(self, obj):
        """
        刷新对象，从数据库重新加载数据

        Args:
            obj: 要刷新的数据库对象
        """
        try:
            await self.db_session.refresh(obj)
            logger.debug(f"{self.__class__.__name__} 刷新对象成功")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 刷新对象失败: {e}")
            raise

    async def execute(self, query, params: "Optional[Dict[str, Any]]" = None):
        """
        执行SQL查询

        Args:
            query: SQLAlchemy查询对象
            params: 查询参数

        Returns:
            查询结果
        """
        return await self.db_session.execute(query, params)

    async def add(self, obj):
        """
        添加对象到会话

        Args:
            obj: 要添加的数据库对象
        """
        await self.db_session.add(obj)
        logger.debug(f"{self.__class__.__name__} 添加对象到会话")

    async def delete(self, obj):
        """
        从会话中删除对象

        Args:
            obj: 要删除的数据库对象
        """
        await self.db_session.delete(obj)
        logger.debug(f"{self.__class__.__name__} 从会话中删除对象")

    async def get(self, model_class, identifier):
        """
        根据ID获取对象

        Args:
            model_class: 模型类
            identifier: 主键ID

        Returns:
            数据库对象或None
        """
        return await self.db_session.get(model_class, identifier)


class SessionManagedService(BaseService):
    """
    会话自管理服务类

    适用于需要独立管理数据库会话的场景，如后台任务、脚本等。
    与BaseService的区别在于，这个类总是自己创建和管理会话。
    """

    def __init__(self):
        """
        初始化会话自管理服务
        """
        super().__init__(db_session=None)
        # 总是需要关闭自己创建的会话
        self._should_close_session = True
        self._session_manager = None

    async def __aenter__(self):
        """异步上下文管理器入口，创建会话"""
        from src.core.database import get_async_db

        # 使用异步上下文管理器获取会话
        self._session_manager = get_async_db()
        self._db_session = await self._session_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，清理会话"""
        if self._session_manager:
            await self._session_manager.__aexit__(exc_type, exc_val, exc_tb)
            self._db_session = None
            self._session_manager = None

    @property
    def db_session(self) -> AsyncSession:
        """
        获取数据库会话

        Returns:
            AsyncSession: 当前可用的数据库会话

        Raises:
            RuntimeError: 如果没有可用的数据库会话
        """
        if self._db_session is None:
            raise RuntimeError(
                f"{self.__class__.__name__} 没有活跃的数据库会话。"
                f"请使用 'async with service:' 模式或手动调用 await service.__aenter__()。"
            )
        return self._db_session


__all__ = [
    "BaseService",
    "SessionManagedService",
]
