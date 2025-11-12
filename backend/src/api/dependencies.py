"""
API依赖注入 - 完整版，包含认证、分页、排序等功能
"""

from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import TokenError, verify_token
from src.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # 不自动抛出错误，允许自定义处理
)


async def get_current_user_optional(
        token: Optional[str] = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前认证用户（可选）"""
    if not token:
        return None

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        stmt = select(User).filter(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return user

    except TokenError:
        return None


async def get_current_user_required(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前认证用户（必需）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except TokenError:
        raise credentials_exception

    stmt = select(User).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )

    return user


# Pydantic 模型用于分页和排序
class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    limit: int = Field(20, ge=1, le=100, description="每页数量，最大100")
    sort: Optional[str] = Field(None, description="排序字段")
    order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.limit

    @field_validator('order')
    @classmethod
    def validate_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('order必须是asc或desc')
        return v


class PaginationResponse(BaseModel):
    """分页响应"""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


async def get_pagination_params(
        page: int = Query(1, ge=1, description="页码"),
        limit: int = Query(20, ge=1, le=100, description="每页数量"),
        sort: Optional[str] = Query(None, description="排序字段"),
        order: str = Query("desc", regex="^(asc|desc)$", description="排序方向")
) -> PaginationParams:
    """获取分页参数"""
    return PaginationParams(page=page, limit=limit, sort=sort, order=order)


def create_pagination_response(
        items: List[Any],
        total: int,
        pagination: PaginationParams
) -> Dict[str, Any]:
    """创建分页响应"""
    total_pages = ceil(total / pagination.limit) if total > 0 else 1

    return {
        "items": items,
        "pagination": PaginationResponse(
            page=pagination.page,
            limit=pagination.limit,
            total=total,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1
        )
    }


# 常用依赖组合
def get_authenticated_user():
    """获取认证用户"""
    return Depends(get_current_user_required)


def get_optional_user():
    """获取可选认证用户"""
    return Depends(get_current_user_optional)


def get_pagination():
    """获取分页参数"""
    return Depends(get_pagination_params)


# 安全相关的依赖
def get_current_active_user(
        current_user: User = Security(get_current_user_required)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user


def get_current_verified_user(
        current_user: User = Security(get_current_active_user)
) -> User:
    """获取当前已验证用户"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户邮箱未验证"
        )
    return current_user


__all__ = [
    "get_current_user_optional",
    "get_current_user_required",
    "get_current_active_user",
    "get_current_verified_user",
    "get_authenticated_user",
    "get_optional_user",
    "get_pagination_params",
    "get_pagination",
    "get_db",
    "create_pagination_response",
    "PaginationParams",
    "PaginationResponse",
]
