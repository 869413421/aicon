"""
生成历史记录相关 API Schema
"""

from typing import Optional
from pydantic import BaseModel, UUID4, field_validator
from datetime import datetime, timedelta
import uuid


class GenerationHistoryResponse(BaseModel):
    """生成历史记录响应"""
    id: str
    resource_type: str
    resource_id: str
    media_type: str
    result_url: str  # 已签名的URL
    prompt: str
    model: Optional[str] = None
    is_selected: bool
    created_at: datetime
    
    @field_validator("id", "resource_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将UUID类型转换为字符串"""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class SelectHistoryRequest(BaseModel):
    """选择历史记录请求"""
    history_id: str
