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

    async def _generate_transition_prompt(
        self,
        from_shot_description: str,
        from_shot_dialogue: str,
        from_shot_characters: list,
        to_shot_description: str,
        to_shot_dialogue: str,
        to_shot_characters: list,
        character_details: dict,  # {character_name: visual_traits}
        api_key,
        model: str = None
    ) -> str:
        """
        生成过渡视频提示词（内部方法，可复用）
        
        Args:
            from_shot_description: 起始分镜描述
            from_shot_dialogue: 起始分镜对话
            from_shot_characters: 起始分镜角色列表
            to_shot_description: 结束分镜描述
            to_shot_dialogue: 结束分镜对话
            to_shot_characters: 结束分镜角色列表
            character_details: 角色详细信息字典
            api_key: API Key对象
            model: 模型名称
            
        Returns:
            str: 生成的视频提示词
        """
        llm_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        from src.services.movie_prompts import MoviePromptTemplates

        # 构建角色信息
        character_info = ""
        all_characters = set(from_shot_characters or []) | set(to_shot_characters or [])
        if all_characters and character_details:
            char_descriptions = []
            for char_name in all_characters:
                if char_name in character_details:
                    char_descriptions.append(f"- {char_name}: {character_details[char_name]}")
            if char_descriptions:
                character_info = "\n\n角色信息：\n" + "\n".join(char_descriptions)

        combined_text = f"""分镜1:
{from_shot_description}
对话: {from_shot_dialogue}
角色: {', '.join(from_shot_characters) if from_shot_characters else '无'}

分镜2:
{to_shot_description}
对话: {to_shot_dialogue}
角色: {', '.join(to_shot_characters) if to_shot_characters else '无'}{character_info}
"""

        prompt = MoviePromptTemplates.get_transition_video_prompt(combined_text)

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
        # 加载API Key
        from src.models.chapter import Chapter
        from src.models.movie import MovieCharacter
        
        scene = await self.db_session.get(MovieScene, from_shot.scene_id, options=[
            selectinload(MovieScene.script)
        ])
        chapter = await self.db_session.get(Chapter, scene.script.chapter_id, options=[
            selectinload(Chapter.project)
        ])
        
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        # 加载角色信息
        character_details = {}
        all_characters = set(from_shot.characters or []) | set(to_shot.characters or [])
        if all_characters:
            stmt = select(MovieCharacter).where(
                MovieCharacter.project_id == chapter.project_id,
                MovieCharacter.name.in_(all_characters)
            )
            result = await self.db_session.execute(stmt)
            characters = result.scalars().all()
            character_details = {char.name: char.visual_traits for char in characters if char.visual_traits}
        
        return await self._generate_transition_prompt(
            from_shot_description=from_shot.shot,
            from_shot_dialogue=from_shot.dialogue or '无',
            from_shot_characters=from_shot.characters or [],
            to_shot_description=to_shot.shot,
            to_shot_dialogue=to_shot.dialogue or '无',
            to_shot_characters=to_shot.characters or [],
            character_details=character_details,
            api_key=api_key,
            model=model
        )

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
        model: str = None,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        批量创建剧本所有分镜的过渡视频（并发处理）
        
        Args:
            script_id: 剧本ID
            api_key_id: API Key ID
            model: 模型名称
            max_concurrent: 最大并发数
            
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

        # 4. 预加载API Key和项目信息（避免在协程中访问数据库）
        from src.models.chapter import Chapter
        from src.models.movie import MovieCharacter
        
        scene = await self.db_session.get(MovieScene, all_shots[0].scene_id, options=[
            selectinload(MovieScene.script)
        ])
        chapter = await self.db_session.get(Chapter, scene.script.chapter_id, options=[
            selectinload(Chapter.project)
        ])
        
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))

        # 5. 预加载所有角色信息
        character_details = {}
        all_character_names = set()
        for shot in all_shots:
            if shot.characters:
                all_character_names.update(shot.characters)
        
        if all_character_names:
            stmt = select(MovieCharacter).where(
                MovieCharacter.project_id == chapter.project_id,
                MovieCharacter.name.in_(all_character_names)
            )
            result = await self.db_session.execute(stmt)
            characters = result.scalars().all()
            character_details = {char.name: char.visual_traits for char in characters if char.visual_traits}
            logger.info(f"加载了 {len(character_details)} 个角色的视觉信息")

        # 6. 准备需要创建的过渡任务（提取所有需要的数据）
        transition_tasks = []
        skipped_count = 0
        
        for i in range(len(all_shots) - 1):
            from_shot = all_shots[i]
            to_shot = all_shots[i + 1]
            from_shot_id = str(from_shot.id)
            to_shot_id = str(to_shot.id)
            
            # 检查是否已存在
            if (from_shot_id, to_shot_id) in existing_pairs:
                logger.info(f"跳过已存在的过渡: {from_shot_id} -> {to_shot_id}")
                skipped_count += 1
                continue
            
            # 提取分镜数据（避免在协程中访问ORM对象）
            transition_tasks.append({
                'order_index': i + 1,
                'from_shot_id': from_shot_id,
                'to_shot_id': to_shot_id,
                'from_shot_description': from_shot.shot,
                'from_shot_dialogue': from_shot.dialogue or '无',
                'from_shot_characters': from_shot.characters or [],
                'to_shot_description': to_shot.shot,
                'to_shot_dialogue': to_shot.dialogue or '无',
                'to_shot_characters': to_shot.characters or [],
            })

        if not transition_tasks:
            return {
                "success": 0,
                "failed": 0,
                "skipped": skipped_count,
                "total": len(all_shots) - 1,
                "message": f"所有过渡已存在，跳过 {skipped_count} 个"
            }

        logger.info(f"准备并发创建 {len(transition_tasks)} 个过渡")

        # 7. 并发worker函数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _create_transition_worker(task_data: Dict[str, Any]):
            async with semaphore:
                try:
                    # 生成LLM提示词（使用提取的方法）
                    video_prompt = await self._generate_transition_prompt(
                        from_shot_description=task_data['from_shot_description'],
                        from_shot_dialogue=task_data['from_shot_dialogue'],
                        from_shot_characters=task_data['from_shot_characters'],
                        to_shot_description=task_data['to_shot_description'],
                        to_shot_dialogue=task_data['to_shot_dialogue'],
                        to_shot_characters=task_data['to_shot_characters'],
                        character_details=character_details,
                        api_key=api_key,
                        model=model
                    )
                    
                    # 创建过渡对象（不立即提交）
                    transition = MovieShotTransition(
                        script_id=script_id,
                        from_shot_id=task_data['from_shot_id'],
                        to_shot_id=task_data['to_shot_id'],
                        order_index=task_data['order_index'],
                        video_prompt=video_prompt,
                        status="pending"
                    )
                    
                    logger.info(f"生成过渡提示词: {task_data['from_shot_id']} -> {task_data['to_shot_id']}")
                    return {"success": True, "transition": transition}
                    
                except Exception as e:
                    logger.error(f"创建过渡失败 {task_data['from_shot_id']} -> {task_data['to_shot_id']}: {e}")
                    return {"success": False, "error": str(e)}

        # 7. 并发执行
        results = await asyncio.gather(*[_create_transition_worker(task) for task in transition_tasks])

        # 8. 批量保存成功的过渡
        success_count = 0
        failed_count = 0
        
        for result in results:
            if result.get("success") and result.get("transition"):
                self.db_session.add(result["transition"])
                success_count += 1
            else:
                failed_count += 1

        # 9. 一次性提交
        if success_count > 0:
            await self.db_session.commit()

        total_possible = len(all_shots) - 1
        logger.info(f"批量创建完成: 新建 {success_count}, 失败 {failed_count}, 跳过 {skipped_count}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total": total_possible,
            "message": f"创建完成: 新建 {success_count}, 跳过 {skipped_count}"
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
