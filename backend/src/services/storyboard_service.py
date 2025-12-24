"""
分镜提取服务 - 从场景提取分镜头
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.core.logging import get_logger
from src.models.movie import MovieScript, MovieScene, MovieShot, MovieCharacter
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService

logger = get_logger(__name__)

class StoryboardService(BaseService):
    """
    分镜提取服务
    从场景提取分镜，每个分镜关联角色列表
    """

    async def extract_shots_from_scene(
        self,
        scene_id: str,
        api_key_id: str,
        model: str = None
    ) -> List[MovieShot]:
        """
        从单个场景提取分镜
        
        Args:
            scene_id: 场景ID
            api_key_id: API Key ID
            model: 模型名称
            
        Returns:
            List[MovieShot]: 生成的分镜列表
        """
        # 1. 加载场景
        scene = await self.db_session.get(MovieScene, scene_id, options=[
            selectinload(MovieScene.script)
        ])
        if not scene:
            raise ValueError(f"未找到场景: {scene_id}")

        # 2. 加载项目角色
        from src.models.chapter import Chapter
        chapter = await self.db_session.get(Chapter, scene.script.chapter_id, options=[
            selectinload(Chapter.project)
        ])
        
        stmt = select(MovieCharacter).where(MovieCharacter.project_id == chapter.project_id)
        result = await self.db_session.execute(stmt)
        characters = result.scalars().all()
        character_list = [char.name for char in characters]

        # 3. 加载API Key
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        llm_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        # 4. 加载分镜提取prompt
        import os
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            '../../docs/prompts/4.分镜提取prompt.md'
        )
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 5. 格式化prompt
        prompt = prompt_template.format(
            characters=json.dumps(character_list, ensure_ascii=False),
            scene=scene.scene
        )

        # 6. 调用LLM
        response = await llm_provider.completions(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的电影分镜提取专家。只输出JSON。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        
        # 清理代码块标记
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        shot_data = json.loads(content)
        logger.info(f"场景 {scene_id} 提取到 {len(shot_data.get('shots', []))} 个分镜")

        # 7. 保存分镜
        created_shots = []
        for idx, shot_item in enumerate(shot_data.get("shots", [])): # 创建分镜
            shot = MovieShot(
                scene_id=scene.id,
                order_index=shot_item.get("order_index", idx + 1),
                shot=shot_item.get("shot", ""),
                dialogue=shot_item.get("dialogue"),
                characters=shot_item.get("characters", [])
            )
            self.db_session.add(shot)
            created_shots.append(shot)

        await self.db_session.commit()
        return created_shots

    async def batch_extract_shots_from_script(
        self,
        script_id: str,
        api_key_id: str,
        model: str = None,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        批量从剧本的所有场景提取分镜
        
        Args:
            script_id: 剧本ID
            api_key_id: API Key ID
            model: 模型名称
            max_concurrent: 最大并发数
            
        Returns:
            Dict: 统计信息 {success: int, failed: int, total: int}
        """
        # 加载剧本和场景
        script = await self.db_session.get(MovieScript, script_id, options=[
            selectinload(MovieScript.scenes)
        ])
        if not script:
            raise ValueError(f"未找到剧本: {script_id}")

        scenes = script.scenes
        if not scenes:
            return {"success": 0, "failed": 0, "total": 0}

        logger.info(f"开始批量提取分镜: {len(scenes)} 个场景")

        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_scene(scene: MovieScene):
            async with semaphore:
                try:
                    await self.extract_shots_from_scene(str(scene.id), api_key_id, model)
                    return {"success": True, "scene_id": str(scene.id)}
                except Exception as e:
                    logger.error(f"场景 {scene.id} 分镜提取失败: {e}")
                    return {"success": False, "scene_id": str(scene.id), "error": str(e)}

        tasks = [process_scene(scene) for scene in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed_count = len(results) - success_count

        logger.info(f"批量分镜提取完成: 成功 {success_count}, 失败 {failed_count}")

        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(scenes),
            "details": results
        }

__all__ = ["StoryboardService"]
