"""
API v1 模块
"""

from fastapi import APIRouter

# 创建主路由器
api_router = APIRouter()


@api_router.get("/")
async def api_v1_info():
    """API v1 信息"""
    return {
        "name": "AICG内容分发平台 API v1",
        "version": "1.0.0",
        "status": "under_development",
        "message": "API v1 正在开发中",
    }


# 导入相关路由
from .auth import router as auth_router
from .users import router as users_router
from .projects import router as projects_router
from .files import router as files_router
from .chapters import router as chapters_router
from .paragraphs import router as paragraphs_router

# 注册路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(files_router, prefix="/files", tags=["文件管理"])
api_router.include_router(projects_router, prefix="/projects", tags=["项目管理"])
api_router.include_router(chapters_router, prefix="/chapters", tags=["章节管理"])
api_router.include_router(paragraphs_router, prefix="/paragraphs", tags=["段落管理"])

__all__ = ["api_router"]
