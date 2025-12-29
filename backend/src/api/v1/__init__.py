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
from .sentences import router as sentences_router
from .api_keys import router as api_keys_router
from .prompt import router as prompt_router
from .image import router as image_router
from .audio import router as audio_router
from .bgms import router as bgms_router
from .tasks import router as tasks_router
from .video_tasks import router as video_tasks_router
from .dashboard import router as dashboard_router
from .bilibili import router as bilibili_router
from .export import router as export_router
# 电影生成功能 - 拆分为4个模块
from .movie_characters import router as movie_characters_router
from .movie_scenes import router as movie_scenes_router
from .movie_shots import router as movie_shots_router
from .movie_transitions import router as movie_transitions_router
from .generation_history import router as generation_history_router

# 注册路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(files_router, prefix="/files", tags=["文件管理"])
api_router.include_router(projects_router, prefix="/projects", tags=["项目管理"])
api_router.include_router(chapters_router, prefix="/chapters", tags=["章节管理"])
api_router.include_router(paragraphs_router, prefix="/paragraphs", tags=["段落管理"])
api_router.include_router(sentences_router, prefix="/sentences", tags=["句子管理"])
api_router.include_router(api_keys_router, prefix="/api-keys", tags=["API密钥管理"])
api_router.include_router(prompt_router, prefix="/prompt", tags=["AI导演引擎"])
api_router.include_router(image_router, prefix="/image", tags=["图片生成"])
api_router.include_router(audio_router, prefix="/audio", tags=["音频生成"])
api_router.include_router(bgms_router, prefix="/bgms", tags=["BGM管理"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(video_tasks_router, prefix="/video-tasks", tags=["视频任务"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(bilibili_router, prefix="/bilibili", tags=["Bilibili发布"])
api_router.include_router(export_router, prefix="/export", tags=["导出功能"])
# 电影生成功能路由
api_router.include_router(movie_characters_router, prefix="/movie", tags=["电影-角色管理"])
api_router.include_router(movie_scenes_router, prefix="/movie", tags=["电影-场景管理"])
api_router.include_router(movie_shots_router, prefix="/movie", tags=["电影-分镜管理"])
api_router.include_router(movie_transitions_router, prefix="/movie", tags=["电影-过渡视频"])
api_router.include_router(generation_history_router, prefix="/movie", tags=["电影-生成历史"])

__all__ = ["api_router"]
