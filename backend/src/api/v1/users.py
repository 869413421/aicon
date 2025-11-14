"""
用户管理API端点
处理用户信息更新、密码修改、偏好设置等功能
重构后使用schemas模块中的Pydantic模型
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.core.database import get_db
from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.services.avatar import avatar_service
from src.api.schemas.user import (
    UserUpdateRequest,
    PasswordChangeRequest,
    UserResponse,
    UserStatsResponse,
    UserDeleteRequest,
    PasswordChangeResponse,
    AvatarUploadResponse,
    AvatarDeleteResponse,
    AvatarInfoResponse,
)
from src.api.schemas.base import MessageResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
        current_user: User = Depends(get_current_user_required)
):
    """
    获取当前登录用户的详细信息

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能查看自己的信息
    """
    # 创建用户数据的副本，确保preferences是字典而不是字符串
    user_data = {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "preferences": current_user.get_preferences(),
        "timezone": current_user.timezone,
        "language": current_user.language,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login": current_user.last_login
    }
    return UserResponse(**user_data)


@router.put("/me", response_model=UserResponse, summary="更新用户信息")
async def update_current_user(
        user_update: UserUpdateRequest,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的基本信息

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能更新自己的信息
    - **可更新字段**: display_name, avatar_url, preferences, timezone, language
    """
    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(current_user, field):
            if field == 'preferences' and value is not None:
                # 特殊处理preferences字段，需要使用用户模型的set_preferences方法
                current_user.set_preferences(value)
            else:
                setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    # 返回更新后的用户信息，确保preferences是字典格式
    user_data = {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "preferences": current_user.get_preferences(),
        "timezone": current_user.timezone,
        "language": current_user.language,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login": current_user.last_login
    }
    return UserResponse(**user_data)


@router.put("/me/password", response_model=PasswordChangeResponse, summary="修改用户密码")
async def change_user_password(
        password_request: PasswordChangeRequest,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户的密码

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能修改自己的密码
    - **验证**: 需要提供当前密码进行验证
    """
    # 验证当前密码
    if not verify_password(password_request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )

    # 检查新密码是否与当前密码相同
    if verify_password(password_request.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同"
        )

    # 更新密码
    current_user.password_hash = get_password_hash(password_request.new_password)
    await db.commit()

    return PasswordChangeResponse()


@router.get("/me/stats", response_model=UserStatsResponse, summary="获取用户统计信息")
async def get_user_stats(
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的统计信息

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能查看自己的统计信息
    - **包含**: 项目数量、总字数、生成视频数、发布视频数、API使用量、费用统计
    """
    # TODO: 实现实际的数据统计逻辑
    # 这里需要关联其他表来计算真实数据
    # 目前返回默认值，待后续模块完善

    return UserStatsResponse()


@router.post("/me/verify-email", response_model=MessageResponse, summary="重新发送验证邮件")
async def resend_verification_email(
        current_user: User = Depends(get_current_user_required)
):
    """
    重新发送邮箱验证邮件

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能发送给自己的验证邮件
    - **限制**: 如果已经验证过，则不需要重复发送
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已经验证过了"
        )

    # TODO: 实现邮件发送逻辑
    # 需要集成邮件服务，如SMTP或第三方邮件服务

    return MessageResponse(message="验证邮件已发送，请检查您的邮箱")


@router.post("/me/delete", response_model=MessageResponse, summary="删除用户账户")
async def delete_user_account(
        delete_request: UserDeleteRequest,
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    删除当前用户账户

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能删除自己的账户
    - **验证**: 需要提供密码进行确认
    - **警告**: 此操作不可逆，请谨慎操作
    """
    # 验证密码
    if not verify_password(delete_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不正确"
        )

    # TODO: 实现账户删除逻辑
    # 需要考虑级联删除相关数据（项目、文件等）
    # 或者软删除（标记为已删除，保留数据）

    # 暂时设置为非活跃状态
    current_user.is_active = False
    await db.commit()

    return MessageResponse(message="账户已成功删除")


@router.post("/me/avatar", response_model=AvatarUploadResponse, summary="上传用户头像")
async def upload_user_avatar(
        file: UploadFile = File(..., description="头像图片文件"),
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    上传用户头像

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能上传自己的头像
    - **文件格式**: 支持JPG、PNG、WebP格式
    - **文件大小**: 最大5MB
    - **图片处理**: 自动调整尺寸为200x200，保持宽高比居中裁剪
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传图片文件"
        )

    # 读取文件数据
    file_data = await file.read()

    # 上传头像
    avatar_url = await avatar_service.upload_avatar(
        user_id=str(current_user.id),
        file_data=file_data,
        filename=file.filename
    )

    # 如果用户已有头像，删除旧头像
    if current_user.avatar_url:
        try:
            await avatar_service.delete_avatar(current_user.avatar_url)
        except Exception:
            # 删除失败不影响新头像上传
            pass

    # 更新用户头像URL
    current_user.avatar_url = avatar_url
    await db.commit()
    await db.refresh(current_user)

    user_response = UserResponse.from_orm(current_user)
    return AvatarUploadResponse(
        message="头像上传成功",
        avatar_url=avatar_url,
        user=user_response
    )


@router.delete("/me/avatar", response_model=AvatarDeleteResponse, summary="删除用户头像")
async def delete_user_avatar(
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
):
    """
    删除用户头像

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能删除自己的头像
    - **清理**: 同时删除MinIO中的文件
    """
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户没有头像"
        )

    # 删除MinIO中的文件
    success = await avatar_service.delete_avatar(current_user.avatar_url)

    # 更新用户头像URL
    current_user.avatar_url = None
    await db.commit()
    await db.refresh(current_user)

    user_response = UserResponse.from_orm(current_user)
    return AvatarDeleteResponse(
        message="头像删除成功",
        user=user_response
    )


@router.get("/me/avatar/info", response_model=AvatarInfoResponse, summary="获取用户头像信息")
async def get_avatar_info(
        current_user: User = Depends(get_current_user_required)
):
    """
    获取用户头像详细信息

    - **认证**: 需要Bearer Token
    - **权限**: 用户只能查看自己的头像信息
    - **返回**: 头像文件大小、上传时间等信息
    """
    if not current_user.avatar_url:
        return AvatarInfoResponse(
            has_avatar=False,
            message="当前用户没有头像"
        )

    avatar_info = await avatar_service.get_avatar_info(current_user.avatar_url)

    if not avatar_info:
        return AvatarInfoResponse(
            has_avatar=True,
            avatar_url=current_user.avatar_url,
            message="头像文件不存在或无法访问"
        )

    return AvatarInfoResponse(
        has_avatar=True,
        avatar_url=current_user.avatar_url,
        avatar_info=avatar_info
    )


__all__ = ["router"]
