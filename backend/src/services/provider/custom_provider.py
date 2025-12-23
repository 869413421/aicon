# src/services/providers/custom_provider.py
import asyncio
import aiohttp
import json
from typing import Any, Dict, List
from openai import AsyncOpenAI

from src.core.logging import get_logger
from src.services.provider.base import BaseLLMProvider, log_provider_call

logger = get_logger(__name__)


class CustomProvider(BaseLLMProvider):
    """
    纯净 SiliconFlow Provider，不含任何业务逻辑。

    - 不拼接 prompt
    - 不封装风格
    - 不理解句子
    - 不处理提示词生成

    只提供 completions() 和 generate_image() 接口 → 等同于一个可并发的 SiliconFlow SDK wrapper
    """

    def __init__(
        self,
        api_key: str,
        max_concurrency: int = 5,
        base_url: str = "https://api.siliconflow.cn/v1",
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.base_url = base_url
        self.api_key = api_key
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @log_provider_call("completions")
    async def completions(
        self, model: str, messages: List[Dict[str, Any]], **kwargs: Any
    ):
        """
        调用 SiliconFlow chat.completions.create（纯粹透传）
        """

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )

    @log_provider_call("generate_image")
    async def generate_image(self, prompt: str, model: str = None, **kwargs: Any):
        """
        调用 自定义 images.generate（纯粹透传）
        如果模型是 gemini-3-pro-image-preview，则调用 generate_image_gemini
        """

        # 检查是否是 Gemini 图像模型
        if model and "gemini" in model.lower():
            # 调用 Gemini 专用方法
            gemini_response = await self.generate_image_gemini(prompt)

            # 将 Gemini 响应包装成兼容格式
            return self._wrap_gemini_response(gemini_response)

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.images.generate(
                model=model or "Kwai-Kolors/Kolors", prompt=prompt, **kwargs
            )

    async def generate_image_with_references(self, prompt: str, reference_images: List[str], model: str = None, **kwargs: Any):
        """
        支持参考图的生图接口
        """
        # 将 reference_images 作为 extra_body 参数传递给 OpenAI SDK
        # 注意: 具体字段名需根据实际厂商 API 调整，这里作为 extra_body 传递
        extra_body = kwargs.pop("extra_body", {})
        if reference_images:
            extra_body["image_prompts"] = reference_images # 适配部分厂商
            extra_body["ref_images"] = reference_images    # 适配部分厂商
        
        return await self.generate_image(prompt, model, extra_body=extra_body, **kwargs)

    @log_provider_call("generate_audio")
    async def generate_audio(
        self, input_text: str, voice: str = "alloy", model: str = "tts-1", **kwargs: Any
    ):
        """
        调用 OpenAI audio.speech.create（纯粹透传）
        """

        # 用 semaphore 限制并发
        async with self.semaphore:
            return await self.client.audio.speech.create(
                model=model, voice=voice, input=input_text, **kwargs
            )

    def _wrap_gemini_response(self, gemini_response: dict):
        """
        将 Gemini 响应包装成兼容 OpenAI 格式的对象

        Gemini API 实际返回格式:
        {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "..."},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "<BASE64>"
                            }
                        }
                    ]
                }
            }]
        }
        """
        try:
            parts = gemini_response["candidates"][0]["content"]["parts"]

            base64_data = None
            mime = None

            # 遍历 parts 查找图片数据
            for part in parts:
                # 检查 inlineData 字段（注意是驼峰命名）
                if "inlineData" in part:
                    base64_data = part["inlineData"]["data"]
                    mime = part["inlineData"]["mimeType"]
                    break

            if not base64_data:
                raise ValueError(
                    "响应中未找到图片数据 (inlineData 或 thoughtSignature)"
                )

            # 创建兼容对象
            class GeminiImageResponse:
                def __init__(self, base64_data, mime):
                    self.data = [GeminiImageData(base64_data, mime)]

            class GeminiImageData:
                def __init__(self, base64_data, mime):
                    self.url = None  # Gemini 不返回 URL
                    self.b64_json = base64_data  # 存储 base64 数据
                    self.mime = mime

            return GeminiImageResponse(base64_data, mime)
        except (KeyError, IndexError) as e:
            raise ValueError(f"无法从 Gemini 响应中提取图像数据: {e}")

    async def generate_image_gemini(self, prompt: str, **kwargs: Any):
        """
        Gemini 生成图像（携程异步版本）
        支持 reference_images 参数 (Persona)
        """
        base_url = self.base_url.replace("/v1", "")
        url = f"{base_url}/v1beta/models/gemini-3-pro-image-preview:generateContent?key={self.api_key}"
        
        # 构造 prompt 部分
        parts = [{"text": prompt}]
        
        # 处理参考图 (Persona)
        reference_images = kwargs.get("reference_images")
        if reference_images:
            import base64
            
            # 最大支持 5 张参考图
            for img_url in reference_images[:5]:
                try:
                    # 下载参考图并转 Base64
                    async with aiohttp.ClientSession() as session:
                        async with session.get(img_url, timeout=10) as resp:
                            if resp.status == 200:
                                img_data = await resp.read()
                                b64_img = base64.b64encode(img_data).decode('utf-8')
                                parts.append({
                                    "inline_data": {
                                        "mime_type": "image/jpeg", # 假设 jpeg, 实际应检测
                                        "data": b64_img
                                    }
                                })
                                logger.info(f"添加参考图到 Gemini 提示词: {img_url}")
                except Exception as e:
                    logger.warning(f"下载参考图失败 {img_url}: {e}")

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        logger.info(f"Gemini 生成图像请求负载: {json.dumps(payload)}")

        async with self.semaphore:  # 控制最大并发
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Gemini API Error: {error_text}")
                        raise ValueError(f"Gemini API 请求失败: {resp.status} - {error_text}")
                        
                    result = await resp.text()
                    return json.loads(result)

    def _wrap_gemini_response(self, gemini_response: dict):
        """
        将 Gemini 图像生成响应转换为 OpenAI 格式
        Gemini 返回: {"candidates": [{"content": {"parts": [{"inlineData": {...}}]}}]}
        OpenAI 格式: {"data": [{"url": "data:image/jpeg;base64,..."}]}
        """
        try:
            # 提取第一个候选结果
            candidate = gemini_response.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            # 查找图像数据部分
            for part in parts:
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    mime_type = inline_data.get("mimeType", "image/jpeg")
                    base64_data = inline_data.get("data", "")
                    
                    # 构造 data URL
                    data_url = f"data:{mime_type};base64,{base64_data}"
                    
                    # 返回 OpenAI 兼容格式
                    from types import SimpleNamespace
                    return SimpleNamespace(
                        data=[SimpleNamespace(url=data_url)]
                    )
            
            # 如果没找到图像数据
            raise ValueError("Gemini 响应中未找到图像数据")
            
        except Exception as e:
            logger.error(f"解析 Gemini 响应失败: {e}, 原始响应: {gemini_response}")
            raise ValueError(f"无法解析 Gemini 图像响应: {e}")

