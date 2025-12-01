"""
AI导演引擎相关的Pydantic模式
"""

from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from .base import UUIDMixin


class PromptGenerateRequest(BaseModel):
    """生成提示词请求模型"""
    chapter_id: UUID = Field(..., description="章节ID")
    api_key_id: UUID = Field(..., description="密钥key_id")
    style: str = Field("cinematic", description="风格预设")
    model: Optional[str] = Field(None, description="模型名称")
    custom_prompt: Optional[str] = Field(None, description="自定义系统提示词")

    model_config = {
        "json_schema_extra": {
            "example": {
                "chapter_id": "123e4567-e89b-12d3-a456-426614174000",
                "api_key_id": "123e4567-e89b-12d3-a456-426614174000",
                "style": "cinematic",
                "model": "deepseek-chat",
                "custom_prompt": "你是一个专业的AI绘画提示词生成专家..."
            }
        }
    }


class PromptGenerateByIdsRequest(BaseModel):
    """生成提示词请求模型"""
    sentence_ids: List[UUID] = Field(..., description="句子ID列表")
    api_key_id: UUID = Field(..., description="密钥key_id")
    style: str = Field("cinematic", description="风格预设")
    model: Optional[str] = Field(None, description="模型名称")
    custom_prompt: Optional[str] = Field(None, description="自定义系统提示词")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sentence_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "223e4567-e89b-12d3-a456-426614174111"
                ],
                "api_key_id": "123e4567-e89b-12d3-a456-426614174000",
                "style": "cinematic",
                "model": "deepseek-chat",
                "custom_prompt": "你是一个专业的AI绘画提示词生成专家..."
            }
        }
    }


class PromptGenerateResponse(BaseModel):
    """生成提示词响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: Optional[str] = Field(None, description="任务ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "成功为 100 个句子生成提示词",
            }
        }
    }


__all__ = [
    "PromptGenerateRequest",
    "PromptGenerateResponse",
    "PromptGenerateByIdsRequest"
]
