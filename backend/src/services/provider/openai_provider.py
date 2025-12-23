# src/services/providers/openai_provider.py

import asyncio
from typing import Any, Dict, List
from openai import AsyncOpenAI

from src.core.logging import get_logger
from src.services.provider.base import BaseLLMProvider, log_provider_call

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    纯净 OpenAI Provider，不含任何业务逻辑。

    - 不拼接 prompt
    - 不封装风格
    - 不理解句子
    - 不处理提示词生成

    只提供 completions() 接口 → 等同于一个可并发的 OpenAI SDK wrapper
    """

    def __init__(self, api_key: str, max_concurrency: int = 5):
        self.client = AsyncOpenAI(api_key=api_key)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @log_provider_call("completions")
    async def completions(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            **kwargs: Any
    ):
        """
        调用 OpenAI chat.completions.create（纯粹透传）
        """

        # 用 semaphore 限制并发
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
        调用 OpenAI images.generate（纯粹透传）
        """
        
        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.images.generate(
                model=model or "dall-e-3",
                prompt=prompt,
                **kwargs
            )

    async def generate_audio(
            self,
            input_text: str,
            voice: str = "alloy",
            model: str = "tts-1",
            **kwargs: Any
    ):
        """
        调用 OpenAI audio.speech.create（纯粹透传）
        """
        
        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=input_text,
                **kwargs
            )
