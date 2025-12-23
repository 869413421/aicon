import httpx
from typing import List, Optional, Dict, Any
from src.core.logging import get_logger
from src.services.provider.base import log_provider_call

logger = get_logger(__name__)

class VectorEngineProvider:
    """
    Vector Engine API 提供商 (api.vectorengine.ai)
    专门用于视频生成任务
    """

    def __init__(self, api_key: str, base_url: str = "https://api.vectorengine.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @log_provider_call("create_video")
    async def create_video(
        self, 
        prompt: str, 
        images: Optional[List[str]] = None, 
        model: str = "veo_3_1-fast", 
        aspect_ratio: str = "16:9",
        enable_upsample: bool = True,
        enhance_prompt: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建视频生成任务
        """
        url = f"{self.base_url}/video/create"
        payload = {
            "prompt": prompt,
            "images": images or [],
            "model": model,
            "aspect_ratio": aspect_ratio,
            "enable_upsample": enable_upsample,
            "enhance_prompt": enhance_prompt
        }
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Vector Engine Create Failed: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Vector Engine Create Error: {e}")
                raise

    @log_provider_call("get_task_status")
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        """
        url = f"{self.base_url}/videos/{task_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Vector Engine Query Status Failed: {e}")
                raise

    @log_provider_call("get_video_content")
    async def get_video_content(self, task_id: str) -> Dict[str, Any]:
        """
        获取视频内容（包含下载链接）
        """
        url = f"{self.base_url}/videos/{task_id}/content"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Vector Engine Get Content Failed: {e}")
                raise
