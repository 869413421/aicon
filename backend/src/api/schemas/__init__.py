"""
API Schemas Package

这个包包含了所有的Pydantic模型定义，按功能模块组织：
- base: 基础模型和通用响应
- auth: 认证相关模型
- user: 用户管理相关模型
- project: 项目管理相关模型
- file: 文件管理相关模型
"""

# 导入基础模型
from .base import (
    MessageResponse,
    SuccessResponse,
    PaginatedResponse,
    ErrorResponse,
    ValidationErrorResponse,
)

# 导入认证相关模型
from .auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenVerifyResponse,
    MessageResponse as AuthMessageResponse,
)

# 导入用户相关模型
from .user import (
    UserUpdateRequest,
    PasswordChangeRequest,
    UserResponse as UserResponseDetailed,
    UserStatsResponse,
    UserDeleteRequest,
    PasswordChangeResponse,
    AvatarUploadResponse,
    AvatarDeleteResponse,
    AvatarInfoResponse,
)

# 导入项目相关模型
from .project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDeleteResponse,
    ProjectArchiveResponse,
    ProjectStatus,
)

# 导入文件相关模型
from .file import (
    FileUploadResponse,
    FileUploadResult,
    FileInfo,
    FileListResponse,
    FileCleanupResponse,
    FileStorageUsageResponse,
    FileBatchDeleteResponse,
    FileIntegrityCheckResult,
    FileIntegrityCheckResponse,
    FileType,
)

# 统一导出所有模型
__all__ = [
    # 基础模型
    "MessageResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "ValidationErrorResponse",

    # 认证模型
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenVerifyResponse",

    # 用户模型
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserStatsResponse",
    "UserDeleteRequest",
    "PasswordChangeResponse",
    "AvatarUploadResponse",
    "AvatarDeleteResponse",
    "AvatarInfoResponse",

    # 项目模型
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectListResponse",
    "ProjectDeleteResponse",
    "ProjectArchiveResponse",
    "ProjectStatus",

    # 文件模型
    "FileUploadResponse",
    "FileUploadResult",
    "FileInfo",
    "FileListResponse",
    "FileCleanupResponse",
    "FileStorageUsageResponse",
    "FileBatchDeleteResponse",
    "FileIntegrityCheckResult",
    "FileIntegrityCheckResponse",
    "FileType",
]

# 为了向后兼容，确保ProjectResponse也被导出
__all__.append("ProjectResponse")