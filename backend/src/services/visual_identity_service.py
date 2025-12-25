"""
视觉身份服务 - 负责角色形象固化（一致性）和场景/首帧图像生成
"""
import asyncio
import uuid
import io
import aiohttp
from typing import List, Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from fastapi import UploadFile

from src.core.logging import get_logger
from src.models.movie import MovieCharacter, MovieShot, MovieScene, MovieScript
from src.models.chapter import Chapter
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService
from src.utils.storage import get_storage_client
from src.services.image import retry_with_backoff

logger = get_logger(__name__)

# ============================================================
# 辅助函数
# ============================================================

# ============================================================
# 独立 Worker 函数 (参照 image.py 规范)
# ============================================================

async def _generate_keyframe_worker(
    shot: MovieShot,
    chars: List[MovieCharacter],
    user_id: Any,
    api_key,
    model: Optional[str],
    semaphore: asyncio.Semaphore
):
    """
    单个分镜关键帧生成的 Worker - 负责生成、下载、上传，不负责 Commit
    角色信息直接从shot.characters字段获取
    
    注意：新架构下，每个分镜只有一个关键帧（keyframe_url）
    """
    import base64
    
    async with semaphore:
        try:
            # 1. 构建专业提示词（包含场景、分镜、角色信息）
            from src.services.keyframe_prompt_builder import KeyframePromptBuilder
            
            # 获取场景信息（shot已经预加载了scene关系）
            scene = shot.scene
            
            final_prompt = KeyframePromptBuilder.build_prompt(
                shot=shot,
                scene=scene,
                characters=chars,
                custom_prompt=None  # worker中不使用自定义提示词
            )
            
            # 2. Provider 调用
            img_provider = ProviderFactory.create(
                provider=api_key.provider,
                api_key=api_key.get_api_key(),
                base_url=api_key.base_url
            )

            logger.info(f"生成分镜 {shot.id} 关键帧, Prompt: {final_prompt[:100]}...")
            
            # 准备生成参数
            gen_params = {
                "prompt": final_prompt,
                "model": model
            }
            
            # 某些 provider 支持参考图 (如 SiliconFlow)        
            result = await retry_with_backoff(
                lambda: img_provider.generate_image(**gen_params)
            )
            
            # 3. 提取并上传图片（使用通用工具函数）
            from src.utils.image_utils import extract_and_upload_image
            
            object_key = await extract_and_upload_image(
                result=result,
                user_id=str(user_id),
                metadata={"shot_id": str(shot.id), "type": "keyframe"}
            )

            # 4. 更新对象属性 (不 Commit) - 使用新的keyframe_url字段
            shot.keyframe_url = object_key
                
            logger.info(f"关键帧生成并存储完成: shot_id={shot.id}, key={object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Worker 生成关键帧失败 [shot_id={shot.id}]: {e}")
            return False


class VisualIdentityService(BaseService):
    """
    视觉身份服务
    要求外部注入 AsyncSession。
    """
    
    def __init__(self, db_session: Any):
        super().__init__(db_session)

    async def generate_character_references(self, character_id: str, api_key_id: str, prompt_override: Optional[str] = None) -> List[str]:
        """
        为角色生成一致性参考图 (单条任务)
        """
        character = await self.db_session.get(MovieCharacter, character_id, options=[joinedload(MovieCharacter.project)])
        if not character: raise ValueError("未找到角色")

        owner_id = str(character.project.owner_id)
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, owner_id)
        
        img_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        base_prompt = f"Character design sheet, {character.name}, {character.visual_traits}, frontal view, profile view, and back view, high quality digital art, consistent features, neutral background."
        final_prompt = prompt_override or base_prompt

        try:
            response = await retry_with_backoff(
                lambda: img_provider.generate_image(
                    prompt=final_prompt,
                    model="flux-pro"
                )
            )
            
            image_url = response.data[0].url
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(image_url) as resp:
                    if resp.status != 200: raise Exception(f"下载失败: {resp.status}")
                    content = await resp.read()

            storage_client = await get_storage_client()
            file_id = str(uuid.uuid4())
            upload_file = UploadFile(
                filename=f"{file_id}.jpg",
                file=io.BytesIO(content),
            )
            
            storage_result = await storage_client.upload_file(
                user_id=owner_id,
                file=upload_file,
                metadata={"character_id": str(character.id), "type": "reference"}
            )
            object_key = storage_result["object_key"]

            character.reference_images = [object_key]
            await self.db_session.commit()
            return [object_key]
            
        except Exception as e:
            logger.error(f"生成角色参考图失败: {e}")
            raise

    async def generate_shot_keyframe(self, shot_id: str, api_key_id: str, model: Optional[str] = None) -> str:
        """为分镜生成关键帧图"""
        shot = await self.db_session.get(MovieShot, shot_id, options=[
            joinedload(MovieShot.scene).joinedload(MovieScene.script).joinedload(MovieScript.chapter).joinedload(Chapter.project)
        ])
        if not shot: raise ValueError("未找到分镜")
        
        project_id = shot.scene.script.chapter.project_id
        user_id = shot.scene.script.chapter.project.owner_id
        
        stmt = select(MovieCharacter).where(MovieCharacter.project_id == project_id)
        chars = (await self.db_session.execute(stmt)).scalars().all()
        
        # 收集角色参考图
        ref_images = _collect_character_references(chars, shot)
        
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(user_id))
        
        storage_client = await get_storage_client()
        semaphore = asyncio.Semaphore(1)
        
        success = await _generate_keyframe_worker(shot, chars, user_id, api_key, model, semaphore, storage_client, ref_images)
        if success:
            await self.db_session.commit()
            return shot.keyframe_url # type: ignore
        else:
            raise Exception("生成分镜关键帧失败")

    # Removed: generate_shot_last_frame - obsolete, shots now only have single keyframe
    # Removed: regenerate_shot_keyframe - use generate_shot_keyframe instead

    async def batch_generate_keyframes(self, script_id: str, api_key_id: str, model: Optional[str] = None) -> dict:
        """
        批量为剧本下的所有分镜生成关键帧
        新架构：每个分镜只有一个关键帧（keyframe_url）
        """
        # 1. 深度加载
        script = await self.db_session.get(MovieScript, script_id, options=[
            selectinload(MovieScript.scenes).selectinload(MovieScene.shots),
            joinedload(MovieScript.chapter).joinedload(Chapter.project)
        ])
        if not script: raise ValueError("剧本不存在")
        
        project_id = script.chapter.project_id
        user_id = script.chapter.project.owner_id
        
        # 2. 预加载角色
        stmt_chars = select(MovieCharacter).where(MovieCharacter.project_id == project_id)
        chars = (await self.db_session.execute(stmt_chars)).scalars().all()

        # 3. 检查所有场景是否都有场景图
        scenes_without_image = [scene for scene in script.scenes if not scene.scene_image_url]
        if scenes_without_image:
            scene_numbers = [scene.order_index for scene in scenes_without_image]
            raise ValueError(
                f"以下场景尚未生成场景图，请先生成场景图: {', '.join(map(str, scene_numbers))}"
            )

        # 4. 准备资源
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(user_id))

        # 5. 筛选待处理任务 - 只生成缺少keyframe的分镜
        tasks = []
        semaphore = asyncio.Semaphore(20)
        
        for scene in script.scenes:
            for shot in scene.shots:
                # 检查是否需要生成关键帧
                if not shot.keyframe_url:
                    tasks.append(
                        _generate_keyframe_worker(shot, chars, user_id, api_key, model, semaphore)
                    )
        
        # 6. 无任务则返回
        if not tasks:
            return {"total": 0, "success": 0, "failed": 0, "message": "所有分镜已有关键帧"}

        # 6. 执行并发
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        failed_count = len(results) - success_count
        
        # 7. 提交
        await self.db_session.commit()
        
        logger.info(f"批量关键帧生成完成: 总计 {len(tasks)}, 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "total": len(tasks),
            "success": success_count,
            "failed": failed_count,
            "message": f"批量生成完成: 成功 {success_count}, 失败 {failed_count}"
        }

    async def generate_single_keyframe(self, shot_id: str, api_key_id: str, model: str = None, prompt: str = None):
        """
        生成单个分镜的关键帧
        
        Args:
            shot_id: 分镜 ID
            api_key_id: API Key ID
            model: 图像模型
            prompt: 自定义提示词（可选）
            
        Returns:
            str: 关键帧图片 URL
        """
        from src.models.movie import MovieShot, MovieScene, MovieScript
        from src.models.chapter import Chapter
        from src.models.project import Project
        from src.services.api_key import APIKeyService
        from src.services.provider.factory import ProviderFactory
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload, joinedload
        
        # 1. 获取分镜（预加载关系）
        stmt = (
            select(MovieShot)
            .where(MovieShot.id == shot_id)
            .options(
                joinedload(MovieShot.scene)
                .joinedload(MovieScene.script)
                .joinedload(MovieScript.chapter)
                .joinedload(Chapter.project)
            )
        )
        result = await self.db_session.execute(stmt)
        shot = result.scalar_one_or_none()
        
        if not shot:
            raise ValueError(f"分镜不存在: {shot_id}")
        
        # 获取user_id
        user_id = str(shot.scene.script.chapter.project.owner_id)
        
        # 2. 获取 API Key  
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id)
        
        if not api_key:
            raise ValueError(f"API Key 不存在: {api_key_id}")
        
        # 3. 创建提供商
        provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )
        
        # 4. 生成图像提示词
        # 单个生成时：前端应该先调用构建器生成专业提示词，用户调整后传递过来
        # 如果前端传递了prompt，直接使用（用户已调整）
        # 如果没有传递，使用构建器生成（兜底逻辑）
        if prompt:
            # 前端传递的提示词（用户已调整）
            final_prompt = prompt
            logger.info(f"使用前端传递的自定义提示词（长度: {len(prompt)}字符）")
        else:
            # 兜底：使用构建器生成专业提示词
            from src.services.keyframe_prompt_builder import KeyframePromptBuilder
            from src.models.movie import MovieCharacter
            from sqlalchemy import select
            
            # 获取角色列表
            project_id = shot.scene.script.chapter.project_id
            stmt_chars = select(MovieCharacter).where(MovieCharacter.project_id == project_id)
            chars_result = await self.db_session.execute(stmt_chars)
            chars = chars_result.scalars().all()
            
            final_prompt = KeyframePromptBuilder.build_prompt(
                shot=shot,
                scene=shot.scene,
                characters=list(chars),
                custom_prompt=None
            )
            logger.info(f"使用构建器生成的专业提示词（长度: {len(final_prompt)}字符）")
        
        # 4.5 获取参考图：场景图 + 角色图
        reference_images = []
        
        # 首先添加场景图（如果存在）
        if shot.scene.scene_image_url:
            reference_images.append(shot.scene.scene_image_url)
            logger.info(f'添加场景参考图: {shot.scene.scene_image_url}')
        else:
            # 不允许生成
            raise ValueError(f'场景 {shot.scene.id} 没有场景图，建议先生成场景图以保持场景一致性')
        
        # 然后添加角色参考图
        if shot.characters:
            from src.models.movie import MovieCharacter
            # 获取角色对象
            project_id = shot.scene.script.chapter.project_id
            stmt_chars = select(MovieCharacter).where(
                MovieCharacter.project_id == project_id,
                MovieCharacter.name.in_(shot.characters)
            )
            chars_result = await self.db_session.execute(stmt_chars)
            characters = chars_result.scalars().all()
            
            # 收集角色的参考图URL
            for char in characters:
                if char.avatar_url:
                    reference_images.append(char.avatar_url)
                    logger.info(f'添加角色 {char.name} 的参考图: {char.avatar_url}')
        
        
        # 注意：无人物场景的禁止元素已在KeyframePromptBuilder中处理
        
        
        
        # 5. 生成图像
        logger.info(f"开始生成关键帧: shot_id={shot_id}, model={model}, 参考图数量={len(reference_images)}")

        if reference_images:

            result = await provider.generate_image(

                prompt=final_prompt,

                model=model,

                reference_images=reference_images

            )

        else:

            result = await provider.generate_image(

                prompt=final_prompt,

                model=model

            )

        # 6. 提取并上传图片（使用通用工具函数，支持base64格式）
        from src.utils.image_utils import extract_and_upload_image
        
        object_key = await extract_and_upload_image(
            result=result,
            user_id=user_id,
            metadata={"shot_id": str(shot_id)}
        )
        
        logger.info(f"图片已上传到存储: {object_key}")
        
        # 7. 更新分镜
        shot.keyframe_url = object_key
        await self.db_session.commit()
        
        logger.info(f"关键帧生成完成: shot_id={shot_id}")
        return object_key

__all__ = ["VisualIdentityService"]


if __name__ == "__main__":
    # 测试关键帧生成
    import asyncio
    
    async def test():
        from src.core.database import get_async_db
        async with get_async_db() as session:
            vis_service = VisualIdentityService(session)
            script_id = "cd1b2680-5d39-4b08-8bf1-968ec05a1571"
            api_key_id = "457f4337-8f54-4749-a2d6-78e1febf9028"
            stats = await vis_service.batch_generate_keyframes(script_id, api_key_id, model="gemini-3-pro-image-preview")
            print(stats)

    asyncio.run(test())