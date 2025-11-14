"""
认证相关的Pydantic模式
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .base import MessageResponse
from .user import UserResponse


class UserRegister(BaseModel):
    """用户注册模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """验证用户名"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePassword123!",
                "display_name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123!"
            }
        }
    }


class TokenResponse(BaseModel):
    """令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: Optional[UserResponse] = Field(None, description="用户信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "uuid-string",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_verified": True,
                    "is_active": True
                }
            }
        }
    }


class TokenVerifyResponse(BaseModel):
    """令牌验证响应模式"""
    valid: bool = Field(True, description="令牌是否有效")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "user_id": "uuid-string",
                "username": "john_doe"
            }
        }
    }


# 为了向后兼容，保留UserResponse的导出
# 但实际使用user模块中的UserResponse


__all__ = [
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenVerifyResponse",
    "MessageResponse",
]
