# src/services/providers/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from functools import wraps
import json
import time
from src.core.logging import get_logger

logger = get_logger(__name__)


def log_provider_call(method_name: str):
    """
    Provider方法调用日志装饰器
    记录请求参数和响应结果,方便调试
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 记录请求开始
            start_time = time.time()
            provider_name = self.__class__.__name__
            
            # 构建请求日志
            request_info = {
                "provider": provider_name,
                "method": method_name,
                "args": _sanitize_for_log(args),
                "kwargs": _sanitize_for_log(kwargs)
            }
            
            logger.info(f"[{provider_name}] {method_name} 请求开始")
            logger.info(f"[{provider_name}] {method_name} 请求参数: {json.dumps(request_info, ensure_ascii=False, indent=2)}")
            
            try:
                # 执行实际方法
                result = await func(self, *args, **kwargs)
                
                # 计算耗时
                elapsed = time.time() - start_time
                
                # 记录响应
                logger.info(f"[{provider_name}] {method_name} 请求成功 (耗时: {elapsed:.2f}s)")
                logger.info(f"[{provider_name}] {method_name} 响应摘要: {_get_response_summary(result)}")
                
                return result
                
            except Exception as e:
                # 计算耗时
                elapsed = time.time() - start_time
                
                # 记录错误
                logger.error(f"[{provider_name}] {method_name} 请求失败 (耗时: {elapsed:.2f}s): {e}")
                
                raise
                
        return wrapper
    return decorator


def _sanitize_for_log(data: Any, max_length: int = 200) -> Any:
    """清理数据用于日志输出,避免敏感信息和过长内容"""
    if isinstance(data, dict):
        return {k: _sanitize_for_log(v, max_length) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [_sanitize_for_log(item, max_length) for item in data]
    elif isinstance(data, str):
        if len(data) > max_length:
            return data[:max_length] + f"... (truncated, total {len(data)} chars)"
        return data
    else:
        return data


def _get_response_summary(response: Any) -> str:
    """获取响应摘要,避免日志过长"""
    try:
        if hasattr(response, '__dict__'):
            attrs = {k: v for k, v in response.__dict__.items() if not k.startswith('_')}
            return f"Object({type(response).__name__}) with {len(attrs)} attributes"
        elif isinstance(response, dict):
            return f"Dict with {len(response)} keys: {list(response.keys())[:5]}"
        elif isinstance(response, (list, tuple)):
            return f"{type(response).__name__} with {len(response)} items"
        else:
            return f"{type(response).__name__}"
    except:
        return "Unknown response type"


class BaseLLMProvider(ABC):
    """
    纯粹 LLM Provider 接口。
    不参杂任何业务、文本处理、拼接逻辑。

    所有 Provider 都必须实现 completions() 方法。
    """

    @abstractmethod
    async def completions(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            **kwargs: Any
    ) -> Any:
        """
        LLM 的 completions 调用（纯粹透传）
        """
        pass

    @abstractmethod
    async def generate_image(
            self,
            prompt: str,
            model: str = None,
            **kwargs: Any
    ) -> Any:
        """
        生成图像的调用（纯粹透传）
        """
        pass

    @abstractmethod
    async def generate_audio(
            self,
            input_text: str,
            voice: str = "alloy",
            model: str = "tts-1",
            **kwargs: Any
    ) -> Any:
        """
        生成音频的调用（纯粹透传）
        """
        pass
