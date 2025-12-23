# src/services/providers/deepseek_provider.py

import asyncio
from typing import Any, Dict, List
from openai import AsyncOpenAI

from src.core.logging import get_logger
from .base import BaseLLMProvider, log_provider_call

logger = get_logger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek 官方 API，兼容 OpenAI Protocol
    """

    def __init__(self, api_key: str, max_concurrency: int = 5):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @log_provider_call("completions")
    async def completions(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            **kwargs: Any
    ):
        async with self.semaphore:
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
    
    @log_provider_call("generate_image")
    async def generate_image(
            self,
            prompt: str,
            model: str = None,
            **kwargs: Any
    ):
        """
        调用 DeepSeek images.generate（纯粹透传）
        """
        
        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.images.generate(
                model=model or "deepseek-r1",
                prompt=prompt,
                **kwargs
            )
