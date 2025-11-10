"""
基础数据模型 - 严格按照原始设计规范实现
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, comment="更新时间")


class UUIDMixin:
    """UUID主键混入类"""
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, comment="主键ID")


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """基础模型类"""
    __abstract__ = True

    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or []
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        return result

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
]