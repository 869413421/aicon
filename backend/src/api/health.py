"""
健康检查API
"""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import psutil

from src.core.database import get_db, engine
from src.core.config import settings
from src.core.logging import logger

router = APIRouter()


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "aicg-backend",
    }


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """数据库连接检查"""
    try:
        # 执行简单查询
        result = await db.execute(text("SELECT 1"))
        row = result.fetchone()

        if row and row[0] == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(status_code=503, detail="数据库查询失败")

    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="数据库连接失败")


@router.get("/redis")
async def redis_health():
    """Redis连接检查"""
    try:
        # 创建Redis连接
        redis_client = redis.from_url(settings.REDIS_URL)

        # 执行ping测试
        result = await redis_client.ping()
        await redis_client.close()

        if result:
            return {
                "status": "healthy",
                "redis": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(status_code=503, detail="Redis ping失败")

    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="Redis连接失败")


@router.get("/celery")
async def celery_health():
    """Celery健康检查"""
    try:
        from src.workers.base import app as celery_app

        # 检查Celery配置
        inspect = celery_app.control.inspect()

        # 获取活跃的workers
        stats = inspect.stats()

        if stats:
            workers = list(stats.keys())
            return {
                "status": "healthy",
                "celery": "connected",
                "workers": workers,
                "worker_count": len(workers),
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "status": "warning",
                "celery": "no_active_workers",
                "message": "没有活跃的Celery workers",
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Celery健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="Celery连接失败")


@router.get("/system")
async def system_health():
    """系统资源健康检查"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用情况
        memory = psutil.virtual_memory()

        # 磁盘使用情况
        disk = psutil.disk_usage('/')

        # 系统负载
        load_avg = psutil.getloadavg()

        # 进程信息
        process = psutil.Process()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2],
                },
            },
            "process": {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "create_time": process.create_time(),
            },
        }

    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="系统信息获取失败")


@router.get("/detailed")
async def detailed_health_check():
    """详细健康检查"""
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "aicg-backend",
        "environment": settings.ENVIRONMENT,
        "checks": {},
        "response_time_ms": 0,
    }

    checks = []

    # 数据库检查
    try:
        from src.core.database import get_db
        async with get_db().__anext__() as db:
            await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
        checks.append("database")
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Redis检查
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = {"status": "healthy"}
        checks.append("redis")
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Celery检查
    try:
        from src.workers.base import app as celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status["checks"]["celery"] = {
                "status": "healthy",
                "workers": list(stats.keys())
            }
            checks.append("celery")
        else:
            health_status["checks"]["celery"] = {
                "status": "warning",
                "message": "no_active_workers"
            }
    except Exception as e:
        health_status["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # 系统资源检查
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # 检查资源使用是否过高
        if cpu_percent > 90 or memory.percent > 90:
            health_status["checks"]["system"] = {
                "status": "warning",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "message": "high resource usage"
            }
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["system"] = {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent
            }
            checks.append("system")

    except Exception as e:
        health_status["checks"]["system"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    health_status["checks_passed"] = len(checks)
    health_status["total_checks"] = 4
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return health_status