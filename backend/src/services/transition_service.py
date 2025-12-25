"""
过渡视频服务 - 生成分镜间过渡视频
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.core.logging import get_logger
from src.models.movie import MovieScript, MovieScene, MovieShot, MovieShotTransition
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService

logger = get_logger(__name__)

class TransitionService(BaseService):
    """
    过渡视频服务
    1. 生成视频提示词（基于两个分镜描述）
    2. 调用视频API生成过渡视频
    """

    async def generate_video_prompt(
        self,
        from_shot: MovieShot,
        to_shot: MovieShot,
        api_key_id: str,
        model: str = None
    ) -> str:
        """
        生成两个分镜之间的视频提示词
        
        Args:
            from_shot: 起始分镜
            to_shot: 结束分镜
            api_key_id: API Key ID
            model: 模型名称
            
        Returns:
            str: 生成的视频提示词（英文）
        """
        # 1. 加载API Key
        from src.models.chapter import Chapter
        scene = await self.db_session.get(MovieScene, from_shot.scene_id, options=[
            selectinload(MovieScene.script)
        ])
        chapter = await self.db_session.get(Chapter, scene.script.chapter_id, options=[
            selectinload(Chapter.project)
        ])
        
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        llm_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        # 2. 使用统一的Prompt模板管理器
        from src.services.movie_prompts import MoviePromptTemplates

        # 3. 组合两个分镜的描述
        combined_text = f"""分镜1:
{from_shot.shot}
对话: {from_shot.dialogue or '无'}

分镜2:
{to_shot.shot}
对话: {to_shot.dialogue or '无'}
"""

        # 4. 使用模板管理器生成prompt
        prompt = MoviePromptTemplates.get_transition_video_prompt(combined_text)

        # 4. 调用LLM生成提示词
        response = await llm_provider.completions(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的电影视频提示词生成专家。"},
                {"role": "user", "content": prompt},
            ]
        )

        video_prompt = response.choices[0].message.content.strip()
        logger.info(f"生成视频提示词: {video_prompt[:100]}...")
        
        return video_prompt

    async def create_transition(
        self,
        script_id: str,
        from_shot_id: str,
        to_shot_id: str,
        order_index: int,
        api_key_id: str,
        model: str = None
    ) -> MovieShotTransition:
        """
        创建过渡视频记录并生成提示词
        
        Args:
            script_id: 剧本ID
            from_shot_id: 起始分镜ID
            to_shot_id: 结束分镜ID
            order_index: 过渡顺序
            api_key_id: API Key ID
            model: 模型名称
            
        Returns:
            MovieShotTransition: 创建的过渡记录
        """
        # 加载分镜
        from_shot = await self.db_session.get(MovieShot, from_shot_id)
        to_shot = await self.db_session.get(MovieShot, to_shot_id)
        
        if not from_shot or not to_shot:
            raise ValueError("分镜不存在")

        # 生成视频提示词
        video_prompt = await self.generate_video_prompt(from_shot, to_shot, api_key_id, model)

        # 创建过渡记录
        transition = MovieShotTransition(
            script_id=script_id,
            from_shot_id=from_shot_id,
            to_shot_id=to_shot_id,
            order_index=order_index,
            video_prompt=video_prompt,
            status="pending"
        )
        
        self.db_session.add(transition)
        await self.db_session.commit()
        
        return transition

    async def batch_create_transitions(
        self,
        script_id: str,
        api_key_id: str,
        model: str = None
    ) -> Dict[str, Any]:
        """
        批量创建剧本所有分镜的过渡视频
        
        Args:
            script_id: 剧本ID
            api_key_id: API Key ID
            model: 模型名称
            
        Returns:
            Dict: 统计信息
        """
        # 1. 加载剧本和所有分镜
        script = await self.db_session.get(MovieScript, script_id, options=[
            selectinload(MovieScript.scenes).selectinload(MovieScene.shots)
        ])
        if not script:
            raise ValueError(f"未找到剧本: {script_id}")

        # 2. 收集所有分镜并按顺序排列，只保留有关键帧的分镜
        all_shots = []
        for scene in sorted(script.scenes, key=lambda s: s.order_index):
            for shot in sorted(scene.shots, key=lambda s: s.order_index):
                # 只添加有关键帧的分镜
                if shot.keyframe_url:
                    all_shots.append(shot)

        if len(all_shots) < 2:
            return {"success": 0, "failed": 0, "total": 0, "message": "有关键帧的分镜数量不足（需要至少2个）"}

        logger.info(f"找到 {len(all_shots)} 个有关键帧的分镜，准备创建 {len(all_shots) - 1} 个过渡")

        # 3. 查询已存在的过渡
        stmt = select(MovieShotTransition).where(MovieShotTransition.script_id == script_id)
        result = await self.db_session.execute(stmt)
        existing_transitions = result.scalars().all()
        
        # 创建已存在过渡的集合（用于快速查找）
        existing_pairs = {(str(t.from_shot_id), str(t.to_shot_id)) for t in existing_transitions}
        logger.info(f"已存在 {len(existing_transitions)} 个过渡")

        # 4. 创建过渡（跳过已存在的）
        created_transitions = []
        skipped_count = 0
        
        for i in range(len(all_shots) - 1):
            from_shot_id = str(all_shots[i].id)
            to_shot_id = str(all_shots[i + 1].id)
            
            # 检查是否已存在
            if (from_shot_id, to_shot_id) in existing_pairs:
                logger.info(f"跳过已存在的过渡: {from_shot_id} -> {to_shot_id}")
                skipped_count += 1
                continue
            
            try:
                transition = await self.create_transition(
                    script_id=script_id,
                    from_shot_id=from_shot_id,
                    to_shot_id=to_shot_id,
                    order_index=i + 1,
                    api_key_id=api_key_id,
                    model=model
                )
                created_transitions.append(transition)
                logger.info(f"创建过渡 {i+1}: {from_shot_id} -> {to_shot_id}")
            except Exception as e:
                logger.error(f"创建过渡 {i+1} 失败: {e}")

        total_possible = len(all_shots) - 1
        return {
            "success": len(created_transitions),
            "failed": total_possible - len(created_transitions) - skipped_count,
            "skipped": skipped_count,
            "total": total_possible,
            "message": f"创建完成: 新建 {len(created_transitions)}, 跳过 {skipped_count}"
        }

    async def generate_transition_video(
        self,
        transition_id: str,
        api_key_id: str,
        video_model: str = "veo_3_1-fast"
    ) -> str:
        """
        生成过渡视频
        
        Args:
            transition_id: 过渡ID
            api_key_id: API Key ID
            video_model: 视频模型
            
        Returns:
            str: 视频任务ID
        """
        # 1. 加载过渡记录
        transition = await self.db_session.get(MovieShotTransition, transition_id, options=[
            selectinload(MovieShotTransition.from_shot),
            selectinload(MovieShotTransition.to_shot)
        ])
        if not transition:
            raise ValueError(f"未找到过渡: {transition_id}")

        # 2. 验证关键帧存在
        if not transition.from_shot.keyframe_url or not transition.to_shot.keyframe_url:
            raise ValueError("分镜关键帧未生成")

        # 3. 加载API Key
        from src.models.chapter import Chapter
        scene = await self.db_session.get(MovieScene, transition.from_shot.scene_id, options=[
            selectinload(MovieScene.script)
        ])
        chapter = await self.db_session.get(Chapter, scene.script.chapter_id, options=[
            selectinload(Chapter.project)
        ])
        
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        video_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        # 4. 调用视频生成API
        result = await video_provider.generate_video(
            prompt=transition.video_prompt,
            first_frame=transition.from_shot.keyframe_url,
            last_frame=transition.to_shot.keyframe_url,
            model=video_model
        )

        # 5. 更新过渡记录
        transition.video_task_id = result.get("task_id")
        transition.status = "processing"
        await self.db_session.commit()

        logger.info(f"过渡视频生成任务已提交: {transition.video_task_id}")
        return transition.video_task_id

__all__ = ["TransitionService"]
