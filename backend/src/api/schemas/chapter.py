"""
章节相关的Pydantic模式
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import PaginatedResponse, UUIDMixin


class ChapterCreate(BaseModel):
    """创建章节请求模型"""
    title: str = Field(..., min_length=1, max_length=500, description="章节标题")
    content: str = Field(..., min_length=1, description="章节原始内容")
    chapter_number: int = Field(..., ge=1, description="章节序号")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "第一章：开始",
                "content": "这是第一章的内容...",
                "chapter_number": 1
            }
        }
    }


class ChapterUpdate(BaseModel):
    """更新章节请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="章节标题")
    content: Optional[str] = Field(None, min_length=1, description="章节原始内容")
    edited_content: Optional[str] = Field(None, description="用户编辑后的内容")
    editing_notes: Optional[str] = Field(None, max_length=1000, description="编辑备注")
    chapter_number: Optional[int] = Field(None, ge=1, description="章节序号")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "更新后的章节标题",
                "content": "更新后的章节内容",
                "edited_content": "用户编辑后的内容",
                "editing_notes": "修改了一些细节"
            }
        }
    }


class ChapterResponse(UUIDMixin):
    """章节响应模型"""
    id: UUID = Field(..., description="章节ID")
    project_id: UUID = Field(..., description="项目ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节原始内容")
    chapter_number: int = Field(..., description="章节序号")
    word_count: int = Field(0, description="字数统计")
    paragraph_count: int = Field(0, description="段落数量")
    sentence_count: int = Field(0, description="句子数量")
    status: str = Field(..., description="处理状态")
    is_confirmed: bool = Field(False, description="是否已确认")
    confirmed_at: Optional[str] = Field(None, description="确认时间")
    edited_content: Optional[str] = Field(None, description="用户编辑后的内容")
    editing_notes: Optional[str] = Field(None, description="编辑备注")
    generation_settings: Optional[str] = Field(None, description="章节级生成配置")
    video_url: Optional[str] = Field(None, description="最终视频URL")
    video_duration: Optional[int] = Field(None, description="视频时长（秒）")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "ChapterResponse":
        """从字典创建响应对象，处理时间格式"""
        # 处理时间字段
        time_fields = ['created_at', 'updated_at', 'confirmed_at']
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
                "project_id": "project-uuid",
                "title": "第一章：开始",
                "content": "这是第一章的内容...",
                "chapter_number": 1,
                "word_count": 1500,
                "paragraph_count": 8,
                "sentence_count": 25,
                "status": "completed",
                "is_confirmed": True,
                "confirmed_at": "2024-01-01T12:00:00Z",
                "edited_content": None,
                "editing_notes": None,
                "generation_settings": None,
                "video_url": "https://example.com/video/chapter1.mp4",
                "video_duration": 180,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }
    }


class ChapterListResponse(PaginatedResponse):
    """章节列表响应模型"""
    chapters: List[ChapterResponse] = Field(..., description="章节列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapters": [
                    {
                        "id": "uuid-string",
                        "title": "第一章：开始",
                        "chapter_number": 1,
                        "status": "completed",
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                ],
                "total": 20,
                "page": 1,
                "size": 20,
                "total_pages": 1
            }
        }
    }


class ChapterDeleteResponse(BaseModel):
    """章节删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    message: str = Field("删除成功", description="响应消息")
    chapter_id: str = Field(..., description="删除的章节ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "删除成功",
                "chapter_id": "uuid-string"
            }
        }
    }


class ChapterConfirmResponse(BaseModel):
    """章节确认响应模型"""
    success: bool = Field(True, description="确认是否成功")
    message: str = Field("章节确认成功", description="响应消息")
    chapter: ChapterResponse = Field(..., description="确认后的章节信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "章节确认成功",
                "chapter": {
                    "id": "uuid-string",
                    "title": "第一章：开始",
                    "is_confirmed": True,
                    "confirmed_at": "2024-01-01T12:00:00Z"
                }
            }
        }
    }


class ChapterStatusResponse(BaseModel):
    """章节状态响应模型"""
    chapter: ChapterResponse = Field(..., description="章节信息")
    can_edit: bool = Field(False, description="是否可以编辑")
    can_confirm: bool = Field(False, description="是否可以确认")
    can_generate: bool = Field(False, description="是否可以生成视频")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapter": {
                    "id": "uuid-string",
                    "title": "第一章：开始",
                    "status": "completed",
                    "is_confirmed": False
                },
                "can_edit": True,
                "can_confirm": True,
                "can_generate": False
            }
        }
    }


__all__ = [
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "ChapterListResponse",
    "ChapterDeleteResponse",
    "ChapterConfirmResponse",
    "ChapterStatusResponse",
]
