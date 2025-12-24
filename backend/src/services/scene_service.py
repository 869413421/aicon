"""
场景提取服务 - 从章节内容提取电影场景
"""

import json
from typing import List, Dict, Any, Optional, Callable
from sqlalchemy.orm import selectinload

from src.core.logging import get_logger
from src.models.movie import MovieScript, MovieScene, ScriptStatus, MovieCharacter
from src.models.chapter import Chapter
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService

logger = get_logger(__name__)

class SceneService(BaseService):
    """
    场景提取服务
    从章节内容提取场景，每个场景关联角色列表
    """

    async def extract_scenes_from_chapter(
        self, 
        chapter_id: str, 
        api_key_id: str, 
        model: str = None,
        on_progress: Callable[[float, str], Any] = None
    ) -> MovieScript:
        """
        从章节提取场景
        
        Args:
            chapter_id: 章节ID
            api_key_id: API Key ID
            model: 模型名称
            on_progress: 进度回调函数
            
        Returns:
            MovieScript: 生成的剧本对象（只包含场景，不包含分镜）
        """
        # 1. 加载章节
        chapter = await self.db_session.get(Chapter, chapter_id, options=[selectinload(Chapter.project)])
        if not chapter:
            raise ValueError(f"未找到章节: {chapter_id}")

        # 2. 加载项目角色
        from sqlalchemy import select
        stmt = select(MovieCharacter).where(MovieCharacter.project_id == chapter.project_id)
        result = await self.db_session.execute(stmt)
        characters = result.scalars().all()
        
        character_list = [char.name for char in characters]
        logger.info(f"项目角色列表: {character_list}")

        # 3. 加载API Key
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        llm_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        # 4. 加载场景提取prompt
        import os
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            '../../docs/prompts/3.场景生成prompt.md'
        )
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 5. 创建剧本记录
        script = MovieScript(chapter_id=chapter.id, status=ScriptStatus.GENERATING)
        self.db_session.add(script)
        await self.db_session.flush()

        try:
            if on_progress:
                await on_progress(0.2, "正在提取场景...")

            # 格式化prompt
            prompt = prompt_template.format(
                characters=json.dumps(character_list, ensure_ascii=False),
                text=chapter.content
            )

            # 调用LLM
            response = await llm_provider.completions(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的电影场景提取专家。只输出JSON。"},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            
            # 清理可能的代码块标记
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            scene_data = json.loads(content)
            logger.info(f"提取到 {len(scene_data.get('scenes', []))} 个场景")

            if on_progress:
                await on_progress(0.6, f"解析场景数据...")

            # 6. 保存场景
            for scene_item in scene_data.get("scenes", []):
                scene = MovieScene(
                    script_id=script.id,
                    order_index=scene_item.get("order_index"),
                    scene=scene_item.get("scene"),
                    characters=scene_item.get("characters", [])
                )
                self.db_session.add(scene)

            script.status = ScriptStatus.COMPLETED
            
            if on_progress:
                await on_progress(0.9, "保存场景数据...")

            await self.db_session.commit()
            
            if on_progress:
                await on_progress(1.0, "场景提取完成")

            logger.info(f"场景提取成功: script_id={script.id}")
            return script

        except Exception as e:
            logger.error(f"场景提取失败: {e}")
            script.status = ScriptStatus.FAILED
            await self.db_session.commit()
            raise

__all__ = ["SceneService"]
