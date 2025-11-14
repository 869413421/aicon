"""
基础Pydantic模式 - 通用响应模型和基础类
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """通用消息响应模式"""
    message: str = Field(..., description="响应消息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "操作成功"
            }
        }
    }


class SuccessResponse(BaseModel):
    """通用成功响应模式"""
    success: bool = Field(True, description="操作是否成功")
    message: Optional[str] = Field(None, description="响应消息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "操作成功"
            }
        }
    }


class PaginatedResponse(BaseModel):
    """分页响应基类"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页大小")
    total_pages: int = Field(..., description="总页数")

    model_config = {
        "from_attributes": True
    }


class ErrorResponse(BaseModel):
    """错误响应模式"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "请求参数验证失败",
                "details": {
                    "field": "username",
                    "reason": "用户名长度不足"
                }
            }
        }
    }


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应模式"""
    error: str = Field("ValidationError", description="错误类型")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="验证错误详情")


__all__ = [
    "MessageResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
]