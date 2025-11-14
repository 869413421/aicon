"""
用户相关的Pydantic模式
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from .base import MessageResponse


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")
    timezone: Optional[str] = Field("Asia/Shanghai", description="时区")
    language: Optional[str] = Field("zh-CN", description="语言")

    @field_validator('preferences', mode='before')
    @classmethod
    def validate_preferences(cls, v):
        if v is not None:
            if isinstance(v, str):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError('preferences必须是有效的JSON字符串')
            elif not isinstance(v, dict):
                raise ValueError('preferences必须是字典或JSON字符串')
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        if v and v not in ["Asia/Shanghai", "UTC", "America/New_York", "Europe/London"]:
            raise ValueError('不支持的时区')
        return v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v and v not in ["zh-CN", "en-US", "ja-JP"]:
            raise ValueError('不支持的语言')
        return v


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    current_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    preferences: Optional[Dict[str, Any]]
    timezone: str
    language: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_serializer('created_at', 'updated_at', 'last_login')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()

    @classmethod
    def from_orm(cls, user) -> "UserResponse":
        """从ORM模型创建响应对象，保持向后兼容"""
        # 处理preferences字段
        preferences = None
        if hasattr(user, 'get_preferences'):
            preferences = user.get_preferences()
        elif hasattr(user, 'preferences'):
            preferences = user.preferences

        return cls(
            id=str(user.id),
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            preferences=preferences,
            timezone=getattr(user, 'timezone', 'Asia/Shanghai'),
            language=getattr(user, 'language', 'zh-CN'),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )


class UserStatsResponse(BaseModel):
    """用户统计信息响应"""
    projects_count: int = Field(0, description="项目总数")
    total_words: int = Field(0, description="总字数")
    generated_videos: int = Field(0, description="生成视频数")
    published_videos: int = Field(0, description="发布视频数")
    api_usage_this_month: float = Field(0.0, description="本月API使用量")
    total_cost: float = Field(0.0, description="总费用")

    model_config = {
        "json_schema_extra": {
            "example": {
                "projects_count": 5,
                "total_words": 100000,
                "generated_videos": 3,
                "published_videos": 2,
                "api_usage_this_month": 15.5,
                "total_cost": 128.90
            }
        }
    }


class UserDeleteRequest(BaseModel):
    """用户账户删除请求"""
    password: str = Field(..., description="确认密码")

    model_config = {
        "json_schema_extra": {
            "example": {
                "password": "CurrentPassword123!"
            }
        }
    }


class PasswordChangeResponse(BaseModel):
    """密码修改响应"""
    message: str = Field("密码修改成功", description="操作结果")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "密码修改成功"
            }
        }
    }


class AvatarUploadResponse(BaseModel):
    """头像上传响应"""
    message: str = Field("头像上传成功", description="操作结果")
    avatar_url: str = Field(..., description="头像URL")
    user: UserResponse = Field(..., description="用户信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "头像上传成功",
                "avatar_url": "https://example.com/avatars/user123.jpg",
                "user": {
                    "id": "uuid-string",
                    "username": "john_doe",
                    "avatar_url": "https://example.com/avatars/user123.jpg"
                }
            }
        }
    }


class AvatarDeleteResponse(BaseModel):
    """头像删除响应"""
    message: str = Field("头像删除成功", description="操作结果")
    user: UserResponse = Field(..., description="用户信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "头像删除成功",
                "user": {
                    "id": "uuid-string",
                    "username": "john_doe",
                    "avatar_url": None
                }
            }
        }
    }


class AvatarInfoResponse(BaseModel):
    """头像信息响应"""
    has_avatar: bool = Field(..., description="是否有头像")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    message: Optional[str] = Field(None, description="状态消息")
    avatar_info: Optional[Dict[str, Any]] = Field(None, description="头像详细信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "has_avatar": True,
                "avatar_url": "https://example.com/avatars/user123.jpg",
                "avatar_info": {
                    "size": 102400,
                    "content_type": "image/jpeg",
                    "last_modified": "2024-01-01T00:00:00Z"
                }
            }
        }
    }


__all__ = [
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserResponse",
    "UserStatsResponse",
    "UserDeleteRequest",
    "PasswordChangeResponse",
    "AvatarUploadResponse",
    "AvatarDeleteResponse",
    "AvatarInfoResponse",
]