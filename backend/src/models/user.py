"""
用户数据模型 - 严格按照原始设计规范实现
"""

from sqlalchemy import Column, String, Boolean, Text, Index, DateTime
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class User(BaseModel):
    """用户模型 - 单一用户模式"""
    __tablename__ = 'users'

    # 基础字段
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    display_name = Column(String(100), nullable=True, comment="显示名称")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    # 状态和权限
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_verified = Column(Boolean, default=False, nullable=False, comment="是否已验证")
    last_login = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")

    # 设置和偏好
    preferences = Column(Text, nullable=True, comment="JSON格式存储偏好设置")
    timezone = Column(String(50), default='Asia/Shanghai', nullable=False, comment="时区")
    language = Column(String(10), default='zh-CN', nullable=False, comment="语言")

    # 时间戳（由BaseModel提供）

    # 关系定义
    # projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    # api_configs = relationship("APIConfig", back_populates="user", cascade="all, delete-orphan")
    # publication_records = relationship("PublicationRecord", back_populates="user")

    def get_preferences(self) -> dict:
        """获取用户偏好设置"""
        if self.preferences:
            try:
                import json
                return json.loads(self.preferences)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def set_preferences(self, preferences: dict) -> None:
        """设置用户偏好"""
        import json
        self.preferences = json.dumps(preferences, ensure_ascii=False)

    @classmethod
    async def get_by_username(cls, db_session, username: str):
        """根据用户名获取用户"""
        from sqlalchemy import select
        result = await db_session.execute(select(cls).filter(cls.username == username))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email(cls, db_session, email: str):
        """根据邮箱获取用户"""
        from sqlalchemy import select
        result = await db_session.execute(select(cls).filter(cls.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def create_user(cls, db_session, username: str, email: str, password: str,
                         display_name: str = None):
        """创建新用户"""
        from src.core.security import get_password_hash, SecurityError

        try:
            password_hash = get_password_hash(password)
        except SecurityError as e:
            raise ValueError(f"密码哈希生成失败: {str(e)}")

        user = cls(
            username=username,
            email=email,
            display_name=display_name,
            password_hash=password_hash
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        from src.core.security import verify_password
        return verify_password(password, self.password_hash)

    def update_last_login(self):
        """更新最后登录时间"""
        from datetime import datetime, timezone
        self.last_login = datetime.now(timezone.utc)


__all__ = [
    "User",
]