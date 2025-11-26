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
    UserResponse,
)
from .base import ErrorResponse, PaginatedResponse, SuccessResponse
from .chapter import (
    ChapterConfirmResponse,
    ChapterCreate,
    ChapterDeleteResponse,
    ChapterListResponse,
    ChapterResponse,
    ChapterStatusResponse,
    ChapterUpdate,
)
from .file import FileDeleteResponse, FileResponse, FileUploadResponse
from .paragraph import (
    ParagraphBatchUpdate,
    ParagraphBatchUpdateItem,
    ParagraphCreate,
    ParagraphDeleteResponse,
    ParagraphListResponse,
    ParagraphResponse,
    ParagraphUpdate,
)
from .project import (
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from .user import PasswordChangeRequest, UserStatsResponse, UserUpdateRequest

__all__ = [
    # Base
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserResponse",
    # User
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserStatsResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDeleteResponse",
    # File
    "FileUploadResponse",
    "FileStorageUsageResponse",
    "FileBatchDeleteResponse",
    "FileIntegrityCheckResult",
    "FileIntegrityCheckResponse",
    "FileType",
]

# 为了向后兼容，确保ProjectResponse也被导出
__all__.append("ProjectResponse")