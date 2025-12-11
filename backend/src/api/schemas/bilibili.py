"""
Bilibili发布API响应模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """发布请求"""
    chapter_id: str = Field(..., description="章节ID")
    title: str = Field(..., min_length=1, max_length=80, description="视频标题")
    desc: str = Field("", max_length=2000, description="视频简介")
    tid: int = Field(171, description="投稿分区ID")
    tag: str = Field("", max_length=500, description="标签,逗号分隔")
    copyright: int = Field(1, ge=1, le=2, description="1原创 2转载")
    source: str = Field("", max_length=200, description="转载来源")
    dynamic: str = Field("", max_length=233, description="空间动态")
    cover_url: str = Field("", description="封面URL")
    dtime: Optional[int] = Field(None, description="延时发布时间戳")
    upload_line: str = Field("kodo", description="上传线路: kodo/bda2/qn/ws")
    upload_limit: int = Field(3, ge=1, le=10, description="并发数")


class PublishResponse(BaseModel):
    """发布响应"""
    success: bool = Field(..., description="是否成功")
    task_id: str = Field(..., description="Celery任务ID")
    publish_task_id: str = Field(..., description="发布任务ID")
    message: str = Field(..., description="提示信息")


class PublishTaskStatus(BaseModel):
    """发布任务状态"""
    id: str = Field(..., description="任务ID")
    chapter_id: str = Field(..., description="章节ID")
    platform: str = Field(..., description="发布平台")
    title: str = Field(..., description="视频标题")
    status: str = Field(..., description="发布状态")
    progress: int = Field(..., description="上传进度 0-100")
    bvid: Optional[str] = Field(None, description="B站BV号")
    aid: Optional[str] = Field(None, description="B站AV号")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    published_at: Optional[datetime] = Field(None, description="发布完成时间")


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool = Field(..., description="是否成功")
    cookie_file: Optional[str] = Field(None, description="cookie文件路径")
    message: str = Field(..., description="提示信息")
    error: Optional[str] = Field(None, description="错误信息")


class TidOption(BaseModel):
    """分区选项"""
    label: str = Field(..., description="分区名称")
    value: int = Field(..., description="分区ID")


__all__ = [
    "PublishRequest",
    "PublishResponse",
    "PublishTaskStatus",
    "LoginResponse",
    "TidOption",
]
