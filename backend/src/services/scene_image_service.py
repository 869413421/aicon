"""
场景图生成服务 - 为每个场景生成无人物的环境参考图
"""
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from src.core.logging import get_logger
from src.models.movie import MovieScene, MovieScript
from src.models.chapter import Chapter
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService
from src.services.image import retry_with_backoff
from src.services.movie_prompts import MoviePromptTemplates

logger = get_logger(__name__)


async def _generate_scene_image_worker(
    scene: MovieScene,
    user_id: Any,
    api_key,
    model: Optional[str],
    semaphore: asyncio.Semaphore,
    custom_prompt: Optional[str] = None
):
    """
    单个场景图生成的 Worker - 负责生成、下载、上传，不负责 Commit
    
    Args:
        scene: 场景对象
        user_id: 用户ID
        api_key: API Key对象
        model: 图像模型
        semaphore: 并发控制信号量
        custom_prompt: 自定义提示词（可选）
    
    Returns:
        bool: 是否成功
    """
    async with semaphore:
        try:
            # 1. 构建场景图提示词
            if custom_prompt:
                final_prompt = custom_prompt
                logger.info(f"使用自定义提示词生成场景图 (scene_id={scene.id})")
            else:
                # 优先使用分镜描述
                if hasattr(scene, 'shots') and scene.shots and len(scene.shots) > 0:
                    # 组合所有分镜描述
                    shots_desc = "\n\n".join([
                        f"Shot {shot.order_index}: {shot.shot}"
                        for shot in sorted(scene.shots, key=lambda x: x.order_index)
                    ])
                    final_prompt = MoviePromptTemplates.get_scene_image_prompt_from_shots(shots_desc)
                    logger.info(f"使用{len(scene.shots)}个分镜描述生成场景图 (scene_id={scene.id})")
                else:
                    # Fallback: 使用原始场景描述
                    final_prompt = MoviePromptTemplates.get_scene_image_prompt(scene.scene)
                    logger.info(f"场景无分镜,使用原始描述生成场景图 (scene_id={scene.id})")
            
            # 保存提示词
            scene.scene_image_prompt = final_prompt
            
            # 2. Provider 调用
            img_provider = ProviderFactory.create(
                provider=api_key.provider,
                api_key=api_key.get_api_key(),
                base_url=api_key.base_url
            )

            logger.info(f"生成场景 {scene.id} 的场景图, Prompt: {final_prompt[:100]}...")
            
            # 准备生成参数
            gen_params = {
                "prompt": final_prompt,
                "model": model
            }
            
            result = await retry_with_backoff(
                lambda: img_provider.generate_image(**gen_params)
            )
            
            # 3. 提取并上传图片
            from src.utils.image_utils import extract_and_upload_image
            
            object_key = await extract_and_upload_image(
                result=result,
                user_id=str(user_id),
                metadata={"scene_id": str(scene.id), "type": "scene_image"}
            )

            # 4. 更新对象属性 (不 Commit)
            scene.scene_image_url = object_key
                
            logger.info(f"场景图生成并存储完成: scene_id={scene.id}, key={object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Worker 生成场景图失败 [scene_id={scene.id}]: {e}")
            return False


class SceneImageService(BaseService):
    """场景图生成服务"""
    
    async def generate_scene_image(
        self, 
        scene_id: str, 
        api_key_id: str, 
        model: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        生成单个场景的场景图
        
        Args:
            scene_id: 场景ID
            api_key_id: API Key ID
            model: 图像模型
            prompt: 自定义提示词（可选）
            
        Returns:
            str: 场景图URL
        """
        # 1. 获取场景（预加载关系）
        stmt = (
            select(MovieScene)
            .where(MovieScene.id == scene_id)
            .options(
                selectinload(MovieScene.shots),  # 加载分镜用于生成场景图
                joinedload(MovieScene.script)
                .joinedload(MovieScript.chapter)
                .joinedload(Chapter.project)
            )
        )
        result = await self.db_session.execute(stmt)
        scene = result.scalar_one_or_none()
        
        if not scene:
            raise ValueError(f"场景不存在: {scene_id}")
        
        # 获取user_id
        user_id = str(scene.script.chapter.project.owner_id)
        
        # 2. 获取 API Key
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, user_id)
        
        if not api_key:
            raise ValueError(f"API Key 不存在: {api_key_id}")
        
        # 3. 生成场景图
        semaphore = asyncio.Semaphore(1)
        success = await _generate_scene_image_worker(
            scene, user_id, api_key, model, semaphore, prompt
        )
        
        if success:
            await self.db_session.commit()
            return scene.scene_image_url
        else:
            raise Exception("生成场景图失败")
    
    async def batch_generate_scene_images(
        self, 
        script_id: str, 
        api_key_id: str, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量生成剧本所有场景的场景图
        
        Args:
            script_id: 剧本ID
            api_key_id: API Key ID
            model: 图像模型
            
        Returns:
            dict: 统计信息 {total: int, success: int, failed: int, message: str}
        """
        # 1. 深度加载
        script = await self.db_session.get(MovieScript, script_id, options=[
            selectinload(MovieScript.scenes).selectinload(MovieScene.shots),  # 加载分镜用于生成场景图
            joinedload(MovieScript.chapter).joinedload(Chapter.project)
        ])
        if not script:
            raise ValueError("剧本不存在")
        
        user_id = script.chapter.project.owner_id
        
        # 2. 准备资源
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(user_id))
        
        # 3. 筛选待处理任务 - 只生成缺少场景图的场景
        tasks = []
        semaphore = asyncio.Semaphore(20)
        
        for scene in script.scenes:
            # 检查是否需要生成场景图
            if not scene.scene_image_url:
                tasks.append(
                    _generate_scene_image_worker(scene, user_id, api_key, model, semaphore)
                )
        
        # 4. 无任务则返回
        if not tasks:
            return {"total": 0, "success": 0, "failed": 0, "message": "所有场景已有场景图"}

        # 5. 执行并发
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        failed_count = len(results) - success_count
        
        # 6. 提交
        await self.db_session.commit()
        
        logger.info(f"批量场景图生成完成: 总计 {len(tasks)}, 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "total": len(tasks),
            "success": success_count,
            "failed": failed_count,
            "message": f"批量生成完成: 成功 {success_count}, 失败 {failed_count}"
        }


__all__ = ["SceneImageService"]
