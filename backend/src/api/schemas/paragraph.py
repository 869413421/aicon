"""
段落相关的Pydantic模式
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .base import PaginatedResponse


class ParagraphCreate(BaseModel):
    """创建段落请求模型"""
    content: str = Field(..., min_length=1, description="段落内容")
    order_index: int = Field(..., ge=1, description="在章节中的顺序")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "这是一个段落的内容...",
                "order_index": 1
            }
        }
    }


class ParagraphUpdate(BaseModel):
    """更新段落请求模型"""
    content: Optional[str] = Field(None, min_length=1, description="段落内容")
    action: Optional[str] = Field(None, description="操作类型: keep, edit, delete, ignore")
    edited_content: Optional[str] = Field(None, description="编辑后的内容")
    ignore_reason: Optional[str] = Field(None, max_length=500, description="忽略原因")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "更新后的段落内容",
                "action": "edit",
                "edited_content": "编辑后的内容",
                "ignore_reason": None
            }
        }
    }


class ParagraphResponse(BaseModel):
    """段落响应模型"""
    id: str = Field(..., description="段落ID")
    chapter_id: str = Field(..., description="章节ID")
    content: str = Field(..., description="段落内容")
    order_index: int = Field(..., description="在章节中的顺序")
    word_count: int = Field(0, description="字数统计")
    sentence_count: int = Field(0, description="句子数量")
    action: str = Field("keep", description="操作类型")
    edited_content: Optional[str] = Field(None, description="编辑后的内容")
    is_confirmed: bool = Field(False, description="是否已确认")
    ignore_reason: Optional[str] = Field(None, description="忽略原因")
    audio_url: Optional[str] = Field(None, description="段落音频URL")
    audio_duration: Optional[int] = Field(None, description="音频时长（秒）")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "ParagraphResponse":
        """从字典创建响应对象，处理时间格式"""
        # 处理时间字段
        time_fields = ['created_at', 'updated_at']
        for field in time_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = data[field].isoformat()
                elif isinstance(data[field], str):
                    pass
                else:
                    data[field] = str(data[field])

        return cls(**data)


class ParagraphBatchUpdateItem(BaseModel):
    """批量更新单个段落项"""
    id: str = Field(..., description="段落ID")
    content: Optional[str] = Field(None, description="段落内容")
    action: Optional[str] = Field(None, description="操作类型")
    edited_content: Optional[str] = Field(None, description="编辑后的内容")
    ignore_reason: Optional[str] = Field(None, description="忽略原因")


class ParagraphBatchUpdate(BaseModel):
    """批量更新段落请求模型"""
    paragraphs: List[ParagraphBatchUpdateItem] = Field(..., description="段落更新列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "paragraphs": [
                    {
                        "id": "uuid-string-1",
                        "action": "keep"
                    },
                    {
                        "id": "uuid-string-2",
                        "content": "更新的内容",
                        "action": "edit"
                    }
                ]
            }
        }
    }


class ParagraphListResponse(PaginatedResponse):
    """段落列表响应模型"""
    paragraphs: List[ParagraphResponse] = Field(..., description="段落列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "paragraphs": [
                    {
                        "id": "uuid-string",
                        "chapter_id": "chapter-uuid",
                        "content": "段落内容",
                        "order_index": 1,
                        "action": "keep",
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


class ParagraphDeleteResponse(BaseModel):
    """段落删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    message: str = Field("删除成功", description="响应消息")
    paragraph_id: str = Field(..., description="删除的段落ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "删除成功",
                "paragraph_id": "uuid-string"
            }
        }
    }


__all__ = [
    "ParagraphCreate",
    "ParagraphUpdate",
    "ParagraphResponse",
    "ParagraphBatchUpdateItem",
    "ParagraphBatchUpdate",
    "ParagraphListResponse",
    "ParagraphDeleteResponse",
]
