"""
电影相关 API Schema
"""

from typing import List, Optional
from pydantic import BaseModel, UUID4, Field, field_validator
from datetime import datetime, timedelta
from src.utils.storage import storage_client

# --- 剧本相关 ---
class ScriptGenerateRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

class ShotExtractRequest(BaseModel):
    """分镜提取请求"""
    api_key_id: str
    model: Optional[str] = None

class ShotBase(BaseModel):
    """分镜基础信息"""
    order_index: int
    shot: Optional[str] = None
    dialogue: Optional[str] = None
    characters: List[str] = []
    keyframe_url: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @field_validator("keyframe_url", mode="after")
    @classmethod
    def sign_urls(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("http"):
            return storage_client.get_presigned_url(v, timedelta(hours=24))
        return v

class MovieShotBase(BaseModel):
    id: UUID4
    order_index: int
    shot: str
    dialogue: Optional[str] = None
    characters: List[str] = []
    keyframe_url: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @field_validator("keyframe_url", mode="after")
    @classmethod
    def sign_urls(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("http"):
            return storage_client.get_presigned_url(v, timedelta(hours=24))
        return v

class MovieSceneBase(BaseModel):
    id: UUID4
    order_index: int
    scene: str
    characters: List[str] = []
    shots: List[MovieShotBase]
    
    class Config:
        from_attributes = True

class MovieScriptResponse(BaseModel):
    id: UUID4
    chapter_id: UUID4
    status: str
    scenes: List[MovieSceneBase]
    class Config:
        from_attributes = True

# --- 角色相关 ---
class MovieCharacterBase(BaseModel):
    id: UUID4
    name: str
    role_description: Optional[str] = None
    visual_traits: Optional[str] = None
    dialogue_traits: Optional[str] = None
    
    # 三视图生成相关字段
    era_background: Optional[str] = None
    occupation: Optional[str] = None
    key_visual_traits: List[str] = []
    generated_prompt: Optional[str] = None
    
    avatar_url: Optional[str] = None
    reference_images: List[str] = []
    
    class Config:
        from_attributes = True
    
    @field_validator("key_visual_traits", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """确保key_visual_traits是列表,将NULL转换为空列表"""
        if v is None:
            return []
        return v
    
    @field_validator("reference_images", mode="before")
    @classmethod
    def ensure_reference_images_list(cls, v):
        """确保reference_images是列表"""
        if v is None:
            return []
        return v
    
    @classmethod
    def from_orm_with_signed_urls(cls, obj):
        """从ORM对象创建，并签名URL"""
        from src.utils.storage import storage_client
        from datetime import timedelta
        
        # 先转换为字典
        data = {
            "id": obj.id,
            "name": obj.name,
            "role_description": obj.role_description,
            "visual_traits": obj.visual_traits,
            "dialogue_traits": obj.dialogue_traits,
            "era_background": obj.era_background,
            "occupation": obj.occupation,
            "key_visual_traits": obj.key_visual_traits or [],
            "generated_prompt": obj.generated_prompt,
            "avatar_url": (
                storage_client.get_presigned_url(obj.avatar_url, timedelta(hours=24))
                if obj.avatar_url and not obj.avatar_url.startswith("http")
                else obj.avatar_url
            ),
            "reference_images": [
                storage_client.get_presigned_url(img, timedelta(hours=24))
                if img and not img.startswith("http")
                else img
                for img in (obj.reference_images or [])
            ]
        }
        return cls(**data)

class CharacterExtractRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

class CharacterUpdateRequest(BaseModel):
    avatar_url: Optional[str] = None
    reference_images: Optional[List[str]] = None

class CharacterGenerateRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None # e.g. "flux-pro"
    style: Optional[str] = "cinematic"
    prompt: Optional[str] = None

class KeyframeGenerateRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

class BatchGenerateAvatarsRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

# --- 生产相关 ---
class ShotProduceRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = "veo_3_1-fast"

class BatchProduceRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

# --- 更新请求 ---
class ShotUpdateRequest(BaseModel):
    shot: Optional[str] = None
    dialogue: Optional[str] = None

# --- 新增请求 schemas ---
class StoryboardExtractRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None

class TransitionGenerateRequest(BaseModel):
    api_key_id: str
    model: Optional[str] = None
    video_model: Optional[str] = "veo_3_1-fast"

