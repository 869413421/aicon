"""
文件类型验证器模块
提供文件类型检测、格式验证、安全检查等功能
"""

import os
import magic
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from src.core.logging import get_logger
from src.models.project import SupportedFileType

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """验证结果类"""
    is_valid: bool
    file_type: Optional[SupportedFileType]
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class FileValidator:
    """文件验证器类"""

    # 支持的文件类型配置
    SUPPORTED_TYPES = {
        SupportedFileType.TXT: {
            'mime_types': ['text/plain'],
            'extensions': ['.txt'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'signatures': [b''],
            'description': '纯文本文档'
        },
        SupportedFileType.MD: {
            'mime_types': ['text/markdown', 'text/plain'],
            'extensions': ['.md', '.markdown'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'signatures': [b'#', b'*', b'-'],
            'description': 'Markdown文档'
        },
        SupportedFileType.DOCX: {
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            'extensions': ['.docx'],
            'max_size': 100 * 1024 * 1024,  # 100MB
            'signatures': [b'PK\x03\x04'],  # ZIP格式
            'description': 'Word文档'
        },
        SupportedFileType.EPUB: {
            'mime_types': ['application/epub+zip'],
            'extensions': ['.epub'],
            'max_size': 200 * 1024 * 1024,  # 200MB
            'signatures': [b'PK\x03\x04'],  # ZIP格式
            'description': 'EPUB电子书'
        }
    }

    # 危险文件扩展名黑名单
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.dll', '.so', '.dylib'
    }

    # 危险MIME类型黑名单
    DANGEROUS_MIME_TYPES = {
        'application/x-executable',
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-shellscript',
        'application/javascript',
        'application/x-java-archive'
    }

    def __init__(self):
        """初始化文件验证器"""
        self.magic_mime = magic.Magic(mime=True)
        self.magic_file = magic.Magic()

    def validate_file(self, file_path: str, expected_type: Optional[SupportedFileType] = None) -> ValidationResult:
        """
        验证文件

        Args:
            file_path: 文件路径
            expected_type: 期望的文件类型

        Returns:
            验证结果
        """
        try:
            if not os.path.exists(file_path):
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message="文件不存在"
                )

            # 基础检查
            basic_check = self._basic_file_check(file_path)
            if not basic_check.is_valid:
                return basic_check

            # 安全检查
            security_check = self._security_check(file_path)
            if not security_check.is_valid:
                return security_check

            # 文件类型检测
            type_check = self._detect_file_type(file_path, expected_type)
            if not type_check.is_valid:
                return type_check

            # 内容验证
            content_check = self._validate_file_content(file_path, type_check.file_type)
            if not content_check.is_valid:
                return content_check

            # 合并所有验证结果
            result = ValidationResult(
                is_valid=True,
                file_type=type_check.file_type,
                metadata={
                    **basic_check.metadata,
                    **type_check.metadata,
                    **content_check.metadata
                },
                warnings=basic_check.warnings + type_check.warnings + content_check.warnings
            )

            logger.info(f"文件验证成功: {file_path}, 类型: {type_check.file_type}")
            return result

        except Exception as e:
            logger.error(f"文件验证失败: {file_path}, 错误: {str(e)}")
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"文件验证失败: {str(e)}"
            )

    def validate_uploaded_file(self, file_content: bytes, filename: str,
                              expected_type: Optional[SupportedFileType] = None) -> ValidationResult:
        """
        验证上传的文件内容

        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            expected_type: 期望的文件类型

        Returns:
            验证结果
        """
        try:
            if not file_content:
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message="文件内容为空"
                )

            # 基础检查
            basic_check = self._basic_uploaded_file_check(file_content, filename)
            if not basic_check.is_valid:
                return basic_check

            # 安全检查
            security_check = self._security_check_content(file_content, filename)
            if not security_check.is_valid:
                return security_check

            # 文件类型检测
            type_check = self._detect_file_type_from_content(
                file_content, filename, expected_type
            )
            if not type_check.is_valid:
                return type_check

            # 内容验证
            content_check = self._validate_file_content_bytes(file_content, type_check.file_type)
            if not content_check.is_valid:
                return content_check

            # 合并所有验证结果
            result = ValidationResult(
                is_valid=True,
                file_type=type_check.file_type,
                metadata={
                    **basic_check.metadata,
                    **type_check.metadata,
                    **content_check.metadata
                },
                warnings=basic_check.warnings + type_check.warnings + content_check.warnings
            )

            logger.info(f"上传文件验证成功: {filename}, 类型: {type_check.file_type}")
            return result

        except Exception as e:
            logger.error(f"上传文件验证失败: {filename}, 错误: {str(e)}")
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"文件验证失败: {str(e)}"
            )

    def _basic_file_check(self, file_path: str) -> ValidationResult:
        """基础文件检查"""
        metadata = {}
        warnings = []

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        metadata['file_size'] = file_size

        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message="文件为空"
            )

        # 检查文件名
        file_name = os.path.basename(file_path)
        if not self._is_valid_filename(file_name):
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message="文件名包含非法字符"
            )

        metadata['filename'] = file_name
        metadata['file_extension'] = Path(file_name).suffix.lower()

        return ValidationResult(
            is_valid=True,
            file_type=None,
            metadata=metadata,
            warnings=warnings
        )

    def _basic_uploaded_file_check(self, file_content: bytes, filename: str) -> ValidationResult:
        """基础上传文件检查"""
        metadata = {}
        warnings = []

        # 检查文件大小
        file_size = len(file_content)
        metadata['file_size'] = file_size

        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message="文件内容为空"
            )

        # 检查文件名
        if not self._is_valid_filename(filename):
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message="文件名包含非法字符"
            )

        metadata['filename'] = filename
        metadata['file_extension'] = Path(filename).suffix.lower()

        return ValidationResult(
            is_valid=True,
            file_type=None,
            metadata=metadata,
            warnings=warnings
        )

    def _security_check(self, file_path: str) -> ValidationResult:
        """安全检查"""
        file_ext = Path(file_path).suffix.lower()

        # 检查危险扩展名
        if file_ext in self.DANGEROUS_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"危险文件类型: {file_ext}"
            )

        # 检查MIME类型
        try:
            mime_type = self.magic_mime.from_file(file_path)
            if mime_type in self.DANGEROUS_MIME_TYPES:
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message=f"危险文件类型: {mime_type}"
                )
        except Exception as e:
            logger.warning(f"无法检测MIME类型: {file_path}, 错误: {e}")

        return ValidationResult(is_valid=True, file_type=None)

    def _security_check_content(self, file_content: bytes, filename: str) -> ValidationResult:
        """安全检查（基于内容）"""
        file_ext = Path(filename).suffix.lower()

        # 检查危险扩展名
        if file_ext in self.DANGEROUS_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"危险文件类型: {file_ext}"
            )

        # 检查MIME类型
        try:
            mime_type = self.magic_mime.from_buffer(file_content)
            if mime_type in self.DANGEROUS_MIME_TYPES:
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message=f"危险文件类型: {mime_type}"
                )
        except Exception as e:
            logger.warning(f"无法检测MIME类型: {filename}, 错误: {e}")

        return ValidationResult(is_valid=True, file_type=None)

    def _detect_file_type(self, file_path: str, expected_type: Optional[SupportedFileType]) -> ValidationResult:
        """检测文件类型"""
        file_ext = Path(file_path).suffix.lower()
        metadata = {}
        warnings = []

        # 基于扩展名检测
        detected_types = []
        for file_type, config in self.SUPPORTED_TYPES.items():
            if file_ext in config['extensions']:
                detected_types.append(file_type)

        # 基于MIME类型检测
        try:
            mime_type = self.magic_mime.from_file(file_path)
            metadata['detected_mime_type'] = mime_type

            for file_type, config in self.SUPPORTED_TYPES.items():
                if mime_type in config['mime_types']:
                    if file_type not in detected_types:
                        detected_types.append(file_type)
        except Exception as e:
            logger.warning(f"无法检测MIME类型: {file_path}, 错误: {e}")

        # 基于文件头检测
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)

            for file_type, config in self.SUPPORTED_TYPES.items():
                for signature in config['signatures']:
                    if header.startswith(signature):
                        if file_type not in detected_types:
                            detected_types.append(file_type)
        except Exception as e:
            logger.warning(f"无法读取文件头: {file_path}, 错误: {e}")

        # 确定最终类型
        if not detected_types:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"不支持的文件类型: {file_ext}"
            )

        if len(detected_types) > 1:
            warnings.append(f"检测到多种可能的文件类型: {detected_types}")

        final_type = detected_types[0]

        # 检查是否符合期望类型
        if expected_type and expected_type != final_type:
            return ValidationResult(
                is_valid=False,
                file_type=final_type,
                error_message=f"文件类型不匹配，期望: {expected_type}, 检测到: {final_type}"
            )

        # 检查文件大小限制
        config = self.SUPPORTED_TYPES[final_type]
        if metadata['file_size'] > config['max_size']:
            return ValidationResult(
                is_valid=False,
                file_type=final_type,
                error_message=f"文件大小超过限制，最大: {config['max_size']}, 当前: {metadata['file_size']}"
            )

        metadata['file_type_description'] = config['description']
        metadata['max_size'] = config['max_size']

        return ValidationResult(
            is_valid=True,
            file_type=final_type,
            metadata=metadata,
            warnings=warnings
        )

    def _detect_file_type_from_content(self, file_content: bytes, filename: str,
                                     expected_type: Optional[SupportedFileType]) -> ValidationResult:
        """从内容检测文件类型"""
        file_ext = Path(filename).suffix.lower()
        metadata = {}
        warnings = []

        # 基于扩展名检测
        detected_types = []
        for file_type, config in self.SUPPORTED_TYPES.items():
            if file_ext in config['extensions']:
                detected_types.append(file_type)

        # 基于MIME类型检测
        try:
            mime_type = self.magic_mime.from_buffer(file_content)
            metadata['detected_mime_type'] = mime_type

            for file_type, config in self.SUPPORTED_TYPES.items():
                if mime_type in config['mime_types']:
                    if file_type not in detected_types:
                        detected_types.append(file_type)
        except Exception as e:
            logger.warning(f"无法检测MIME类型: {filename}, 错误: {e}")

        # 基于文件头检测
        header = file_content[:1024]
        for file_type, config in self.SUPPORTED_TYPES.items():
            for signature in config['signatures']:
                if header.startswith(signature):
                    if file_type not in detected_types:
                        detected_types.append(file_type)

        # 确定最终类型
        if not detected_types:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"不支持的文件类型: {file_ext}"
            )

        if len(detected_types) > 1:
            warnings.append(f"检测到多种可能的文件类型: {detected_types}")

        final_type = detected_types[0]

        # 检查是否符合期望类型
        if expected_type and expected_type != final_type:
            return ValidationResult(
                is_valid=False,
                file_type=final_type,
                error_message=f"文件类型不匹配，期望: {expected_type}, 检测到: {final_type}"
            )

        # 检查文件大小限制
        config = self.SUPPORTED_TYPES[final_type]
        if len(file_content) > config['max_size']:
            return ValidationResult(
                is_valid=False,
                file_type=final_type,
                error_message=f"文件大小超过限制，最大: {config['max_size']}, 当前: {len(file_content)}"
            )

        metadata['file_type_description'] = config['description']
        metadata['max_size'] = config['max_size']

        return ValidationResult(
            is_valid=True,
            file_type=final_type,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_file_content(self, file_path: str, file_type: SupportedFileType) -> ValidationResult:
        """验证文件内容"""
        metadata = {}
        warnings = []

        try:
            # 计算文件哈希
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                metadata['file_hash'] = file_hash

            # 根据文件类型进行特定验证
            if file_type == SupportedFileType.DOCX:
                return self._validate_docx_file(file_path, metadata, warnings)
            elif file_type == SupportedFileType.EPUB:
                return self._validate_epub_file(file_path, metadata, warnings)
            elif file_type in [SupportedFileType.TXT, SupportedFileType.MD]:
                return self._validate_text_file(file_path, metadata, warnings)

        except Exception as e:
            logger.error(f"内容验证失败: {file_path}, 错误: {str(e)}")
            return ValidationResult(
                is_valid=False,
                file_type=file_type,
                error_message=f"内容验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=file_type,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_file_content_bytes(self, file_content: bytes, file_type: SupportedFileType) -> ValidationResult:
        """验证文件内容（基于字节）"""
        metadata = {}
        warnings = []

        try:
            # 计算文件哈希
            file_hash = hashlib.sha256(file_content).hexdigest()
            metadata['file_hash'] = file_hash

            # 根据文件类型进行特定验证
            if file_type == SupportedFileType.DOCX:
                return self._validate_docx_content(file_content, metadata, warnings)
            elif file_type == SupportedFileType.EPUB:
                return self._validate_epub_content(file_content, metadata, warnings)
            elif file_type in [SupportedFileType.TXT, SupportedFileType.MD]:
                return self._validate_text_content(file_content, metadata, warnings)

        except Exception as e:
            logger.error(f"内容验证失败, 错误: {str(e)}")
            return ValidationResult(
                is_valid=False,
                file_type=file_type,
                error_message=f"内容验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=file_type,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_docx_file(self, file_path: str, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证DOCX文件"""
        try:
            import zipfile

            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 检查必要的文件
                required_files = ['[Content_Types].xml', 'word/document.xml']
                for required_file in required_files:
                    if required_file not in zip_file.namelist():
                        return ValidationResult(
                            is_valid=False,
                            file_type=SupportedFileType.DOCX,
                            error_message=f"无效的DOCX文件，缺少必要文件: {required_file}"
                        )

                metadata['zip_entries'] = len(zip_file.namelist())
                metadata['is_valid_docx'] = True

        except zipfile.BadZipFile:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.DOCX,
                error_message="无效的DOCX文件，无法解析ZIP格式"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.DOCX,
                error_message=f"DOCX文件验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.DOCX,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_docx_content(self, file_content: bytes, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证DOCX文件内容"""
        try:
            import zipfile
            from io import BytesIO

            with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_file:
                # 检查必要的文件
                required_files = ['[Content_Types].xml', 'word/document.xml']
                for required_file in required_files:
                    if required_file not in zip_file.namelist():
                        return ValidationResult(
                            is_valid=False,
                            file_type=SupportedFileType.DOCX,
                            error_message=f"无效的DOCX文件，缺少必要文件: {required_file}"
                        )

                metadata['zip_entries'] = len(zip_file.namelist())
                metadata['is_valid_docx'] = True

        except zipfile.BadZipFile:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.DOCX,
                error_message="无效的DOCX文件，无法解析ZIP格式"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.DOCX,
                error_message=f"DOCX文件验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.DOCX,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_epub_file(self, file_path: str, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证EPUB文件"""
        try:
            import zipfile

            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 检查必要的文件
                required_files = ['mimetype', 'META-INF/container.xml']
                for required_file in required_files:
                    if required_file not in zip_file.namelist():
                        return ValidationResult(
                            is_valid=False,
                            file_type=SupportedFileType.EPUB,
                            error_message=f"无效的EPUB文件，缺少必要文件: {required_file}"
                        )

                # 检查mimetype文件
                with zip_file.open('mimetype') as f:
                    mimetype_content = f.read().decode('utf-8').strip()
                    if mimetype_content != 'application/epub+zip':
                        warnings.append(f"EPUB mimetype异常: {mimetype_content}")

                metadata['zip_entries'] = len(zip_file.namelist())
                metadata['is_valid_epub'] = True

        except zipfile.BadZipFile:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.EPUB,
                error_message="无效的EPUB文件，无法解析ZIP格式"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.EPUB,
                error_message=f"EPUB文件验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.EPUB,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_epub_content(self, file_content: bytes, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证EPUB文件内容"""
        try:
            import zipfile
            from io import BytesIO

            with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_file:
                # 检查必要的文件
                required_files = ['mimetype', 'META-INF/container.xml']
                for required_file in required_files:
                    if required_file not in zip_file.namelist():
                        return ValidationResult(
                            is_valid=False,
                            file_type=SupportedFileType.EPUB,
                            error_message=f"无效的EPUB文件，缺少必要文件: {required_file}"
                        )

                # 检查mimetype文件
                with zip_file.open('mimetype') as f:
                    mimetype_content = f.read().decode('utf-8').strip()
                    if mimetype_content != 'application/epub+zip':
                        warnings.append(f"EPUB mimetype异常: {mimetype_content}")

                metadata['zip_entries'] = len(zip_file.namelist())
                metadata['is_valid_epub'] = True

        except zipfile.BadZipFile:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.EPUB,
                error_message="无效的EPUB文件，无法解析ZIP格式"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=SupportedFileType.EPUB,
                error_message=f"EPUB文件验证失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.EPUB,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_text_file(self, file_path: str, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证文本文件"""
        try:
            # 尝试用UTF-8编码读取
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata['encoding'] = 'utf-8'
            metadata['content_length'] = len(content)

            # 检查是否包含二进制内容
            if '\x00' in content:
                warnings.append("文件可能包含二进制内容")
                metadata['has_binary_content'] = True
            else:
                metadata['has_binary_content'] = False

        except UnicodeDecodeError:
            # UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                metadata['encoding'] = 'gbk'
                metadata['content_length'] = len(content)
                warnings.append("文件使用了GBK编码")
            except UnicodeDecodeError:
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message="无法解码文件内容，可能不是有效的文本文件"
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"文本文件读取失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.TXT,
            metadata=metadata,
            warnings=warnings
        )

    def _validate_text_content(self, file_content: bytes, metadata: Dict[str, Any], warnings: List[str]) -> ValidationResult:
        """验证文本文件内容"""
        try:
            # 尝试用UTF-8解码
            content = file_content.decode('utf-8')
            metadata['encoding'] = 'utf-8'
            metadata['content_length'] = len(content)

            # 检查是否包含二进制内容
            if '\x00' in content:
                warnings.append("文件可能包含二进制内容")
                metadata['has_binary_content'] = True
            else:
                metadata['has_binary_content'] = False

        except UnicodeDecodeError:
            # UTF-8解码失败，尝试其他编码
            try:
                content = file_content.decode('gbk')
                metadata['encoding'] = 'gbk'
                metadata['content_length'] = len(content)
                warnings.append("文件使用了GBK编码")
            except UnicodeDecodeError:
                return ValidationResult(
                    is_valid=False,
                    file_type=None,
                    error_message="无法解码文件内容，可能不是有效的文本文件"
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type=None,
                error_message=f"文本文件解码失败: {str(e)}"
            )

        return ValidationResult(
            is_valid=True,
            file_type=SupportedFileType.TXT,
            metadata=metadata,
            warnings=warnings
        )

    def _is_valid_filename(self, filename: str) -> bool:
        """检查文件名是否有效"""
        # 检查非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in illegal_chars:
            if char in filename:
                return False

        # 检查长度
        if len(filename) > 255:
            return False

        # 检查保留名称
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            return False

        return True


# 创建全局验证器实例
file_validator = FileValidator()