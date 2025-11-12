"""
数据库连接和会话管理模块
"""

from typing import AsyncGenerator

from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from src.core.config import settings
from src.core.logging import logger

# 创建基础模型类
Base = declarative_base()

# 全局数据库引擎和会话工厂
engine: AsyncEngine = None
AsyncSessionLocal: async_sessionmaker = None
SessionLocal: sessionmaker = None


async def create_database_engine() -> AsyncEngine:
    """创建数据库引擎"""
    global engine, AsyncSessionLocal, SessionLocal

    logger.info("正在创建数据库引擎...")

    # 创建异步引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # 开发环境下打印SQL
        # 异步引擎使用不同的连接池配置
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        # 连接参数
        connect_args={
            "server_settings": {
                "application_name": settings.APP_NAME,
                "timezone": "UTC",
            },
        },
    )

    # 创建异步会话工厂
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )

    # 创建同步会话工厂（用于Alembic迁移）
    SessionLocal = sessionmaker(
        bind=create_sync_engine(),
        autoflush=True,
        autocommit=False,
    )

    logger.info("数据库引擎创建成功")
    return engine


def create_sync_engine() -> Engine:
    """创建同步数据库引擎（用于Alembic）"""
    from sqlalchemy import create_engine

    return create_engine(
        settings.database_url_sync,
        echo=settings.DEBUG,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）"""
    if AsyncSessionLocal is None:
        await create_database_engine()

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库会话异常: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db_session():
    """获取同步数据库会话（用于Alembic）"""
    if SessionLocal is None:
        create_sync_engine()

    return SessionLocal()


# 数据库事件监听器
async def setup_database_events():
    """设置数据库事件监听器"""
    if engine is None:
        await create_database_engine()

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """设置SQLite连接参数"""
        if "sqlite" in settings.DATABASE_URL:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("数据库事件监听器设置完成")


async def test_database_connection() -> bool:
    """测试数据库连接"""
    try:
        if engine is None:
            await create_database_engine()

        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            row = result.first()
            return row and row[0] == 1

    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False


async def close_database_connections():
    """关闭数据库连接"""
    global engine, AsyncSessionLocal, SessionLocal

    if engine:
        logger.info("正在关闭数据库连接...")
        await engine.dispose()
        engine = None
        AsyncSessionLocal = None
        SessionLocal = None
        logger.info("数据库连接已关闭")


async def create_database_tables():
    """创建所有数据库表（开发环境使用）"""
    if settings.is_production:
        logger.warning("生产环境不应该使用此方法创建表，请使用Alembic迁移")
        return

    try:
        if engine is None:
            await create_database_engine()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("数据库表创建成功")

    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


async def drop_database_tables():
    """删除所有数据库表（仅开发环境使用）"""
    if settings.is_production:
        logger.error("生产环境禁止删除数据库表")
        raise RuntimeError("生产环境禁止删除数据库表")

    try:
        if engine is None:
            await create_database_engine()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("数据库表删除成功")

    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


# 数据库健康检查
async def get_database_stats() -> dict:
    """获取数据库统计信息"""
    try:
        if engine is None:
            await create_database_engine()

        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": "healthy",
        }

    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# 初始化数据库
async def initialize_database():
    """初始化数据库"""
    logger.info("正在初始化数据库...")

    # 创建引擎
    await create_database_engine()

    # 设置事件监听器
    await setup_database_events()

    # 测试连接
    if await test_database_connection():
        logger.info("数据库初始化成功")
    else:
        logger.error("数据库初始化失败")
        raise RuntimeError("数据库连接失败")


# 导出
__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "SessionLocal",
    "get_db",
    "get_db",
    "get_sync_db_session",
    "create_database_engine",
    "test_database_connection",
    "close_database_connections",
    "create_database_tables",
    "drop_database_tables",
    "get_database_stats",
    "initialize_database",
]
