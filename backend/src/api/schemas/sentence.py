"""
句子相关的Pydantic模式
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.sentence import SentenceStatus
from .base import PaginatedResponse, UUIDMixin


class SentenceBase(BaseModel):
    content: str = Field(..., description="句子内容")


class SentenceCreate(SentenceBase):
    """创建句子请求模型"""
    order_index: Optional[int] = Field(None, description="顺序索引，不传则自动追加到最后")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "这是一个句子的内容...",
                "order_index": 1
            }
        }
    }


class SentenceUpdate(BaseModel):
    """更新句子请求模型"""
    content: str = Field(..., description="句子内容")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "更新后的句子内容"
            }
        }
    }


class SentenceResponse(UUIDMixin, SentenceBase):
    """句子响应模型"""
    id: UUID = Field(..., description="句子ID")
    paragraph_id: UUID = Field(..., description="所属段落ID")
    order_index: int = Field(..., description="顺序索引")
    word_count: int = Field(0, description="字数统计")
    character_count: int = Field(0, description="字符数量")
    status: SentenceStatus = Field(..., description="处理状态")
    image_url: Optional[str] = Field(None, description="生成的图片URL")
    image_style: Optional[str] = Field(None, description="图片风格")
    edited_prompt: Optional[str] = Field(None, description="编辑后的提示词")
    audio_url: Optional[str] = Field(None, description="生成的音频URL")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "SentenceResponse":
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


class SentenceListResponse(PaginatedResponse):
    """句子列表响应模型"""
    sentences: List[SentenceResponse] = Field(..., description="句子列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sentences": [
                    {
                        "id": "uuid-string",
                        "paragraph_id": "paragraph-uuid",
                        "content": "句子内容",
                        "order_index": 1,
                        "status": "pending",
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
