# src/services/providers/atlascloud_provider.py

import asyncio
from typing import Any, Dict, List
from openai import AsyncOpenAI

from src.core.logging import get_logger
from src.services.provider.base import BaseLLMProvider, log_provider_call

logger = get_logger(__name__)


class AtlasCloudProvider(BaseLLMProvider):
    """
    Atlas Cloud Provider，OpenAI 兼容，不含任何业务逻辑。

    - 不拼接 prompt
    - 不封装风格
    - 不理解句子
    - 不处理提示词生成

    Atlas Cloud（https://www.atlascloud.ai）是一个全模态 AI 推理平台，
    用一套 OpenAI 兼容 API 即可访问 LLM、图像、视频等 300+ 模型，
    刚好覆盖本项目「剧本 → 分镜提示词 → 图像 → 配音」整条创作链路所需的模型。

    只提供 completions() / generate_image() / generate_audio() 接口
    → 等同于一个可并发的 OpenAI SDK wrapper，base_url 指向 Atlas Cloud。
    """

    def __init__(
        self,
        api_key: str,
        max_concurrency: int = 5,
        base_url: str = "https://api.atlascloud.ai/v1",
    ):
        # 规范化 base_url: 确保以斜杠结尾
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        self.base_url = base_url

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=300.0,  # 5分钟超时
        )
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @log_provider_call("completions")
    async def completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs: Any,
    ):
        """
        调用 Atlas Cloud chat.completions.create（纯粹透传）

        说明：默认模型 deepseek-ai/deepseek-v4-pro 是带推理（reasoning）的模型，
        调用时请给足 max_tokens（建议 >= 512），否则 token 可能先耗在思维链上，
        出现 finish_reason=length 且 content 为空。
        """

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )

    @log_provider_call("generate_image")
    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        **kwargs: Any,
    ):
        """
        调用 Atlas Cloud images.generate（纯粹透传）
        """

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.images.generate(
                model=model or "openai/gpt-image-2/text-to-image",
                prompt=prompt,
                **kwargs,
            )

    @log_provider_call("generate_audio")
    async def generate_audio(
        self,
        input_text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        **kwargs: Any,
    ):
        """
        调用 Atlas Cloud audio.speech.create（纯粹透传）
        """

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=input_text,
                **kwargs,
            )
