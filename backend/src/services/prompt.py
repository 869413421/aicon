"""
AI导演引擎 - 提示词生成服务

提供服务：
- 批量生成图像提示词
- 支持多种LLM提供商（Volcengine、DeepSeek）
- 提示词模板管理
- 风格预设管理

设计原则：
- 异常处理遵循统一策略
- 方法职责单一，保持简洁
"""

from typing import List, Dict, Optional, Any, Coroutine
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.services import ChapterService
from src.services.base import SessionManagedService

logger = get_logger(__name__)


class PromptService(SessionManagedService):
    """
    提示词生成服务
    
    负责调用LLM将小说文本转换为绘画提示词。
    支持多种LLM提供商和风格预设。
    """

    # 风格预设模板
    STYLE_TEMPLATES = {
        "cinematic": "Cinematic lighting, 8k resolution, photorealistic, movie still, detailed texture, dramatic atmosphere.",
        "anime": "Anime style, Makoto Shinkai style, vibrant colors, detailed background, high quality.",
        "illustration": "Digital illustration, artstation, concept art, fantasy style, detailed.",
        "ink": "Chinese ink painting style, watercolor, traditional art, artistic, abstract."
    }



    async def generate_prompts_batch(
            self,
            chapter_id: str,
            api_key_id: str,
            style: str = "cinematic"
    ) -> None:
        """
        批量生成提示词
        
        调用LLM将小说句子转换为英文绘画提示词。
        
        Args:
            chapter_id: 章节ID
            api_key_id: API密钥ID
            style: 风格预设名称
            
        Returns:
            List[Dict]: 包含 prompt 字段的字典列表
            
        Raises:
            BusinessLogicError: 当API调用失败或参数无效时
        """
        # 1.查找出章节
        chapter_server = ChapterService(self.db_session)
        sentences = await chapter_server.get_sentences(chapter_id)

    def _build_system_prompt(self, style: str) -> str:
        """
        构建系统提示词
        
        Args:
            style: 风格预设名称
            
        Returns:
            str: 完整的系统提示词
        """
        base_prompt = """你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的英文Stable Diffusion提示词。

请遵循以下规则：
1. 输出格式必须是纯JSON数组，不要包含markdown标记或其他文字。
2. 数组中每个元素是一个字符串，对应输入的每一句话。
3. 提示词结构：(Subject description), (Action/Pose), (Environment/Background), (Lighting/Atmosphere), (Style modifiers), (Quality tags)
4. 翻译要准确传达原文的意境、情感和视觉要素。
5. 如果句子是心理描写或无具体画面，请生成符合上下文氛围的意象画面。

"""
        style_suffix = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES["cinematic"])
        return base_prompt + f"风格要求：{style_suffix}"


__all__ = ["PromptService"]
