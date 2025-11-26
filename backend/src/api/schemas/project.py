"""
项目相关的Pydantic模式
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.project import ProjectStatus
from .base import PaginatedResponse, UUIDMixin


class ProjectCreate(BaseModel):
    """创建项目请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")
    file_name: Optional[str] = Field(None, max_length=255, description="文件名称")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    file_type: Optional[str] = Field(None, pattern="^(txt|md|docx|epub)$", description="文件类型")
    file_path: Optional[str] = Field(None, max_length=500, description="MinIO存储路径")
    file_hash: Optional[str] = Field(None, max_length=64, description="文件MD5哈希")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "我的小说项目",
                "description": "这是一个关于科幻小说的项目",
                "file_name": "novel.txt",
                "file_size": 1024000,
                "file_type": "txt",
                "file_path": "uploads/user123/files/uuid-file.txt",
                "file_hash": "d41d8cd98f00b204e9800998ecf8427e"
            }
        }
    }


class ProjectUpdate(BaseModel):
    """更新项目请求模型 - 只允许编辑标题和描述"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "更新后的项目标题",
                "description": "更新后的项目描述"
            }
        }
    }


class ProjectResponse(UUIDMixin):
    """项目响应模型"""
    id: UUID = Field(..., description="项目ID")
    owner_id: UUID = Field(..., description="所有者ID")
    title: str = Field(..., description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    file_name: str = Field(..., description="文件名称")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    file_path: str = Field(..., description="MinIO存储路径")
    file_hash: Optional[str] = Field(None, description="文件MD5哈希")
    word_count: int = Field(0, description="字数统计")
    chapter_count: int = Field(0, description="章节数")
    paragraph_count: int = Field(0, description="段落数")
    sentence_count: int = Field(0, description="句子数")
    status: str = Field(..., description="项目状态")
    processing_progress: int = Field(0, description="处理进度（百分比）")
    error_message: Optional[str] = Field(None, description="错误信息")
    generation_settings: Optional[str] = Field(None, description="生成设置（JSON）")
    completed_at: Optional[str] = Field(None, description="完成时间")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectResponse":
        """从字典创建响应对象，处理时间格式"""
        # 处理时间字段
        time_fields = ['created_at', 'updated_at', 'completed_at']
        for field in time_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = data[field].isoformat()
                elif isinstance(data[field], str):
                    # 保持字符串格式
                    pass
                else:
                    data[field] = str(data[field])

        return cls(**data)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "uuid-string",
                "owner_id": "user-uuid",
                "title": "我的小说项目",
                "description": "这是一个关于科幻小说的项目",
                "file_name": "novel.txt",
                "file_size": 1024000,
                "file_type": "txt",
                "file_path": "uploads/user123/files/uuid-file.txt",
                "file_hash": "d41d8cd98f00b204e9800998ecf8427e",
                "word_count": 50000,
                "chapter_count": 20,
                "paragraph_count": 300,
                "sentence_count": 800,
                "status": "completed",
                "processing_progress": 100,
                "error_message": None,
                "generation_settings": None,
                "completed_at": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }
    }


class ProjectListResponse(PaginatedResponse):
    """项目列表响应模型"""
    projects: List[ProjectResponse] = Field(..., description="项目列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "projects": [
                    {
                        "id": "uuid-string",
                        "title": "我的小说项目",
                        "status": "completed",
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                ],
                "total": 10,
                "page": 1,
                "size": 20,
                "total_pages": 1
            }
        }
    }


class ProjectDeleteResponse(BaseModel):
    """项目删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    message: str = Field("删除成功", description="响应消息")
    project_id: str = Field(..., description="删除的项目ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "删除成功",
                "project_id": "uuid-string"
            }
        }
    }


class ProjectArchiveResponse(BaseModel):
    """项目归档响应模型"""
    message: str = Field("项目归档成功", description="操作结果")
    project: ProjectResponse = Field(..., description="归档后的项目信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "项目归档成功",
                "project": {
                    "id": "uuid-string",
                    "title": "我的小说项目",
                    "status": "archived"
                }
            }
        }
    }


class ProjectProcessingResponse(BaseModel):
    """项目处理响应模型 - 用于创建项目后启动处理任务"""
    success: bool = Field(True, description="处理是否成功")
    message: str = Field(..., description="响应消息")
    project: ProjectResponse = Field(..., description="项目信息")
    task_id: Optional[str] = Field(None, description="Celery任务ID")
    processing_status: str = Field(..., description="处理状态")
    can_retry: bool = Field(False, description="是否可以重试")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "项目创建成功，已开始解析",
                "project": {
                    "id": "uuid-string",
                    "title": "我的小说项目",
                    "status": "parsing",
                    "processing_progress": 0
                },
                "task_id": "celery-task-uuid",
                "processing_status": "parsing",
                "can_retry": False
            }
        }
    }


class ProjectRetryResponse(BaseModel):
    """项目重试响应模型"""
    success: bool = Field(True, description="重试是否成功")
    message: str = Field(..., description="响应消息")
    task_id: Optional[str] = Field(None, description="Celery任务ID")
    processing_status: str = Field(..., description="新的处理状态")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "重试任务已提交",
                "task_id": "celery-retry-task-uuid",
                "processing_status": "parsing"
            }
        }
    }


class ProjectStatusResponse(BaseModel):
    """项目状态详细响应模型"""
    project: ProjectResponse = Field(..., description="项目信息")
    processing_details: Optional[dict] = Field(None, description="处理详情（来自Celery任务）")
    task_info: Optional[dict] = Field(None, description="任务信息")
    can_retry: bool = Field(False, description="是否可以重试")
    estimated_time: Optional[int] = Field(None, description="预估剩余时间（秒）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "project": {
                    "id": "uuid-string",
                    "title": "我的小说项目",
                    "status": "parsing",
                    "processing_progress": 45
                },
                "processing_details": {
                    "chapters_count": 12,
                    "paragraphs_count": 156,
                    "sentences_count": 423
                },
                "task_info": {
                    "task_id": "celery-task-uuid",
                    "status": "running"
                },
                "can_retry": False,
                "estimated_time": 120
            }
        }
    }


__all__ = [
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDeleteResponse",
    "ProjectArchiveResponse",
    "ProjectProcessingResponse",
    "ProjectRetryResponse",
    "ProjectStatusResponse",
    "ProjectStatus",
]
