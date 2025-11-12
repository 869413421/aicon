"""
用户认证API端点 - 简化版，只保留核心功能
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.core.config import settings
from src.core.database import get_db
from src.core.security import (
    create_access_token,
    verify_token,
    TokenError
)
from src.models.user import User
from src.api.schemas.auth import (
    UserRegister,
    UserResponse,
    TokenResponse,
    MessageResponse
)

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except TokenError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """用户注册"""
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).filter(
            or_(User.username == user_data.username, User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    # 创建新用户
    user = await User.create_user(
        db_session=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        display_name=user_data.display_name,
    )

    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )

    # 更新最后登录时间
    user.update_last_login()
    await db.commit()

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """用户登出"""
    # JWT无状态认证，客户端删除token即可
    return MessageResponse(message="登出成功")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)


@router.get("/verify-token")
async def verify_current_token(
    current_user: User = Depends(get_current_user)
) -> Any:
    """验证当前令牌有效性"""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username
    }


__all__ = [
    "router",
    "get_current_user",
]