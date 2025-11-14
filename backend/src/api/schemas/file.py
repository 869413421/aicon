"""
文件相关的Pydantic模式
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import PaginatedResponse


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str = Field(..., description="文件唯一标识")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    storage_key: str = Field(..., description="存储路径键")

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_id": "uuid-string",
                "original_filename": "document.txt",
                "file_size": 1024000,
                "file_type": "txt",
                "storage_key": "uploads/user123/files/uuid-file.txt"
            }
        }
    }


class FileUploadResult(BaseModel):
    """文件上传完整响应模型"""
    success: bool = Field(True, description="上传是否成功")
    message: str = Field("文件上传成功", description="响应消息")
    data: FileUploadResponse = Field(..., description="文件信息")
    file_info: Optional[Dict[str, Any]] = Field(None, description="文件处理信息")
    storage_info: Optional[Dict[str, Any]] = Field(None, description="存储信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "file_id": "uuid-string",
                    "original_filename": "document.txt",
                    "file_size": 1024000,
                    "file_type": "txt",
                    "storage_key": "uploads/user123/files/uuid-file.txt"
                },
                "file_info": {
                    "word_count": 5000,
                    "paragraph_count": 25,
                    "encoding": "utf-8"
                },
                "storage_info": {
                    "bucket": "aicg-files",
                    "url": "https://example.com/files/uuid-file.txt"
                }
            }
        }
    }


class FileInfo(BaseModel):
    """文件信息模型"""
    object_key: str = Field(..., description="存储对象键")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    size_mb: float = Field(..., description="文件大小（MB）")
    last_modified: Optional[str] = Field(None, description="最后修改时间")
    url: Optional[str] = Field(None, description="访问URL")
    is_orphaned: bool = Field(False, description="是否为孤立文件")

    model_config = {
        "json_schema_extra": {
            "example": {
                "object_key": "uploads/user123/files/document.txt",
                "filename": "document.txt",
                "size": 1024000,
                "size_mb": 0.98,
                "last_modified": "2024-01-01T12:00:00Z",
                "url": "https://example.com/files/document.txt",
                "is_orphaned": False
            }
        }
    }


class FileListResponse(PaginatedResponse):
    """文件列表响应模型"""
    files: List[FileInfo] = Field(..., description="文件列表")
    orphaned_count: int = Field(0, description="孤立文件数量")

    model_config = {
        "json_schema_extra": {
            "example": {
                "files": [
                    {
                        "object_key": "uploads/user123/files/document.txt",
                        "filename": "document.txt",
                        "size": 1024000,
                        "size_mb": 0.98,
                        "is_orphaned": False
                    }
                ],
                "total_files": 10,
                "page": 1,
                "size": 50,
                "total_pages": 1,
                "orphaned_count": 2
            }
        }
    }


class FileCleanupResponse(BaseModel):
    """文件清理响应模型"""
    success: bool = Field(True, description="清理是否成功")
    dry_run: bool = Field(..., description="是否为试运行")
    found_orphaned_files: int = Field(..., description="发现的孤立文件数")
    deleted_files: int = Field(..., description="删除的文件数")
    total_size_mb: float = Field(..., description="总大小（MB）")
    deleted_size_mb: float = Field(..., description="删除的大小（MB）")
    files: List[Dict[str, Any]] = Field(default_factory=list, description="文件详情")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "dry_run": False,
                "found_orphaned_files": 5,
                "deleted_files": 5,
                "total_size_mb": 10.5,
                "deleted_size_mb": 10.5,
                "files": [
                    {
                        "object_key": "uploads/user123/files/old-file.txt",
                        "size": 2048000,
                        "size_mb": 1.95,
                        "last_modified": "2023-12-01T10:00:00Z"
                    }
                ]
            }
        }
    }


class FileStorageUsageResponse(BaseModel):
    """存储使用情况响应模型"""
    success: bool = Field(True, description="查询是否成功")
    total_files: int = Field(..., description="总文件数")
    total_size_mb: float = Field(..., description="总大小（MB）")
    total_size_gb: float = Field(..., description="总大小（GB）")
    file_type_distribution: Dict[str, int] = Field(default_factory=dict, description="文件类型分布")
    project_stats: Optional[Dict[str, Any]] = Field(None, description="项目统计")
    quota_limit_gb: float = Field(..., description="配额限制（GB）")
    quota_usage_percent: float = Field(..., description="配额使用百分比")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "total_files": 25,
                "total_size_mb": 512.5,
                "total_size_gb": 0.5,
                "file_type_distribution": {
                    "txt": 15,
                    "docx": 8,
                    "md": 2
                },
                "project_stats": {
                    "total_projects": 10,
                    "active_projects": 5
                },
                "quota_limit_gb": 10.0,
                "quota_usage_percent": 5.13
            }
        }
    }


class FileBatchDeleteResponse(BaseModel):
    """批量文件删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    requested_files: int = Field(..., description="请求删除的文件数")
    valid_files: int = Field(..., description="有效文件数")
    protected_files: int = Field(..., description="受保护的文件数")
    deleted_files: int = Field(..., description="实际删除的文件数")
    failed_files: int = Field(..., description="删除失败的文件数")
    deleted_keys: List[str] = Field(default_factory=list, description="成功删除的文件键")
    failed_keys: List[str] = Field(default_factory=list, description="删除失败的文件键")
    protected_keys: List[str] = Field(default_factory=list, description="受保护的文件键")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "requested_files": 5,
                "valid_files": 3,
                "protected_files": 2,
                "deleted_files": 3,
                "failed_files": 0,
                "deleted_keys": [
                    "uploads/user123/files/file1.txt",
                    "uploads/user123/files/file2.txt",
                    "uploads/user123/files/file3.txt"
                ],
                "failed_keys": [],
                "protected_keys": [
                    "uploads/user123/files/protected-file.txt",
                    "uploads/user123/files/project-file.txt"
                ]
            }
        }
    }


class FileIntegrityCheckResult(BaseModel):
    """文件完整性检查结果模型"""
    project_id: str = Field(..., description="项目ID")
    project_title: str = Field(..., description="项目标题")
    file_exists: bool = Field(..., description="文件是否存在")
    file_size_match: Optional[bool] = Field(None, description="文件大小是否匹配")
    file_hash_match: Optional[bool] = Field(None, description="文件哈希是否匹配")
    storage_size: Optional[int] = Field(None, description="存储中的文件大小")
    project_size: Optional[int] = Field(None, description="项目记录的文件大小")
    error: Optional[str] = Field(None, description="错误信息")

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": "uuid-string",
                "project_title": "我的小说项目",
                "file_exists": True,
                "file_size_match": True,
                "file_hash_match": True,
                "storage_size": 1024000,
                "project_size": 1024000,
                "error": None
            }
        }
    }


class FileIntegrityCheckResponse(BaseModel):
    """文件完整性检查响应模型"""
    success: bool = Field(True, description="检查是否成功")
    project_id: Optional[str] = Field(None, description="指定的项目ID")
    total_checked: int = Field(..., description="检查的项目总数")
    files_exist: int = Field(..., description="存在的文件数")
    files_missing: int = Field(..., description="缺失的文件数")
    size_mismatch: int = Field(..., description="大小不匹配的文件数")
    hash_mismatch: int = Field(..., description="哈希不匹配的文件数")
    integrity_score: float = Field(..., description="完整性评分（百分比）")
    results: List[FileIntegrityCheckResult] = Field(..., description="详细检查结果")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "project_id": None,
                "total_checked": 10,
                "files_exist": 8,
                "files_missing": 2,
                "size_mismatch": 1,
                "hash_mismatch": 0,
                "integrity_score": 70.0,
                "results": [
                    {
                        "project_id": "uuid-string",
                        "project_title": "我的小说项目",
                        "file_exists": True,
                        "file_size_match": True,
                        "file_hash_match": True,
                        "error": None
                    }
                ]
            }
        }
    }


# 文件类型枚举
class FileType(str):
    """支持的文件类型枚举"""
    TXT = "txt"
    MD = "md"
    DOCX = "docx"
    EPUB = "epub"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        allowed_types = [cls.TXT, cls.MD, cls.DOCX, cls.EPUB]
        if v not in allowed_types:
            raise ValueError(f"不支持的文件类型: {v}. 支持的类型: {', '.join(allowed_types)}")
        return v

    @classmethod
    def get_mime_type(cls, file_type: str) -> str:
        """获取文件类型对应的MIME类型"""
        mime_types = {
            cls.TXT: "text/plain",
            cls.MD: "text/markdown",
            cls.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            cls.EPUB: "application/epub+zip"
        }
        return mime_types.get(file_type, "application/octet-stream")


__all__ = [
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