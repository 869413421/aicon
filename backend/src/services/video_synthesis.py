"""
视频合成服务 - 视频生成的核心服务（重构版）
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from src.core.exceptions import BusinessLogicError
from src.core.logging import get_logger
from src.models import Chapter, ChapterStatus, Sentence, VideoTask, VideoTaskStatus
from src.services.api_key import APIKeyService
from src.services.base import SessionManagedService
from src.services.chapter import ChapterService
from src.services.video_composition_service import video_composition_service
from src.services.video_task import VideoTaskService
from src.utils.ffmpeg_utils import (
    check_ffmpeg_installed,
    concatenate_videos,
    get_audio_duration,
)
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class VideoSynthesisService(SessionManagedService):
    """
    视频合成服务（重构版）

    负责视频生成的完整流程编排，将具体操作委托给专门的服务：
    - SubtitleService: 字幕生成和LLM纠错
    - MaterialService: 素材下载
    - VideoCompositionService: 视频合成
    """

    def __init__(self):
        """初始化视频合成服务"""
        super().__init__()
        self.storage_client = None
        logger.debug("VideoSynthesisService 初始化完成")

    async def _get_storage_client(self):
        """获取存储客户端"""
        if self.storage_client is None:
            self.storage_client = await get_storage_client()
        return self.storage_client

    async def _validate_chapter_materials(self, chapter: Chapter) -> None:
        """
        验证章节素材是否准备好

        Args:
            chapter: 章节对象

        Raises:
            BusinessLogicError: 如果章节状态不正确或素材不完整
        """
        # 检查章节状态
        if chapter.status != ChapterStatus.MATERIALS_PREPARED.value:
            raise BusinessLogicError(
                f"章节状态不正确，当前状态: {chapter.status}，需要: {ChapterStatus.MATERIALS_PREPARED.value}"
            )

        # 获取章节的所有句子
        chapter_service = ChapterService(self.db_session)
        sentences = await chapter_service.get_sentences(chapter.id)

        if not sentences:
            raise BusinessLogicError("章节没有句子")

        # 检查每个句子是否有必要的素材
        missing_materials = []
        for sentence in sentences:
            if not sentence.image_url:
                missing_materials.append(f"句子 {sentence.id} 缺少图片")
            if not sentence.audio_url:
                missing_materials.append(f"句子 {sentence.id} 缺少音频")

        if missing_materials:
            raise BusinessLogicError(
                f"章节素材不完整:\n" + "\n".join(missing_materials[:5])  # 只显示前5个
            )

        logger.info(f"章节素材验证通过: {chapter.id}, 共 {len(sentences)} 个句子")

    async def _process_sentence_async(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict,
            semaphore: asyncio.Semaphore,
            api_key=None,
            model: Optional[str] = None
    ) -> Tuple[bool, Optional[Path], Optional[Exception]]:
        """
        异步处理单个句子（带并发控制）

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置
            semaphore: 并发控制信号量
            api_key: API密钥（可选，用于LLM纠错）
            model: 模型名称（可选）

        Returns:
            (是否成功, 视频路径, 异常对象)
        """
        async with semaphore:
            try:
                video_path = await video_composition_service.synthesize_sentence_video(
                    sentence=sentence,
                    temp_dir=temp_dir,
                    index=index,
                    gen_setting=gen_setting,
                    api_key=api_key,
                    model=model
                )
                return True, video_path, None
            except Exception as e:
                logger.error(f"处理句子失败: {sentence.id}, 错误: {e}")
                return False, None, e

    # 保留原有的方法签名以兼容测试代码
    async def _synthesize_sentence_video(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict
    ) -> Path:
        """
        合成单个句子的视频（兼容方法）

        这个方法保留是为了兼容现有的测试代码。
        实际实现已经移到 VideoCompositionService。

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置

        Returns:
            生成的视频文件路径
        """
        return await video_composition_service.synthesize_sentence_video(
            sentence=sentence,
            temp_dir=temp_dir,
            index=index,
            gen_setting=gen_setting,
            api_key=None,  # 测试时不使用LLM纠错
            model=None
        )

    # ==================== 视频缓存管理方法 ====================

    async def _upload_sentence_video_cache(
            self,
            video_path: Path,
            sentence_id: str,
            user_id: str
    ) -> str:
        """
        上传单句视频到 MinIO 作为缓存
        
        Args:
            video_path: 本地视频文件路径
            sentence_id: 句子ID
            user_id: 用户ID
            
        Returns:
            MinIO对象键
        """
        storage_client = await self._get_storage_client()
        object_key = f"sentence_videos/{sentence_id}.mp4"
        
        await storage_client.upload_file_from_path(
            user_id=user_id,
            file_path=str(video_path),
            original_filename=f"{sentence_id}.mp4",
            object_key=object_key,
            metadata={"content_type": "video/mp4"}
        )
        
        logger.info(f"✅ 句子视频已缓存: {object_key}")
        return object_key

    async def _download_cached_video(
            self,
            sentence: Sentence,
            temp_dir: Path
    ) -> Path:
        """
        从 MinIO 下载缓存的句子视频
        
        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            
        Returns:
            下载后的本地视频路径
        """
        storage_client = await self._get_storage_client()
        video_path = temp_dir / f"cached_{sentence.id}.mp4"
        
        # 下载视频
        content = await storage_client.download_file(sentence.sentence_video_key)
        
        with open(video_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"📥 已下载缓存视频: {sentence.sentence_video_key}")
        return video_path

    async def _get_video_duration(self, video_path: Path) -> int:
        """
        获取视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
        """
        try:
            # get_audio_duration 是同步函数，不需要 await
            duration = get_audio_duration(str(video_path))
            return int(duration) if duration else 5
        except Exception as e:
            logger.warning(f"获取视频时长失败: {e}，使用默认值5秒")
            return 5

    async def _process_sentence_with_cache(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict,
            semaphore: asyncio.Semaphore,
            user_id: str,
            api_key=None,
            model: Optional[str] = None
    ) -> Tuple[bool, Optional[Path], Optional[Exception]]:
        """
        处理单个句子：生成视频并上传缓存
        
        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置
            semaphore: 并发控制信号量
            user_id: 用户ID
            api_key: API密钥
            model: 模型名称
            
        Returns:
            (是否成功, 视频路径, 异常对象)
        """
        async with semaphore:
            try:
                # 1. 生成视频
                video_path = await video_composition_service.synthesize_sentence_video(
                    sentence=sentence,
                    temp_dir=temp_dir,
                    index=index,
                    gen_setting=gen_setting,
                    api_key=api_key,
                    model=model
                )
                
                # 2. 上传到 MinIO 作为缓存
                video_key = await self._upload_sentence_video_cache(
                    video_path, str(sentence.id), user_id
                )
                
                # 3. 获取视频时长
                duration = await self._get_video_duration(video_path)
                
                # 4. 保存缓存信息到数据库
                # 注意：这里只更新对象状态，不要 flush，避免并发 flush 导致 "Session is already flushing" 错误
                # 统一在主流程中 flush
                sentence.save_video_cache(video_key, duration)
                
                logger.info(f"✅ 句子 {index} 视频已生成并缓存")
                return True, video_path, None
                
            except Exception as e:
                logger.error(f"❌ 处理句子 {index} 失败: {e}")
                return False, None, e

    def _merge_video_paths(
            self,
            sentences: list,
            generated_videos: dict,
            cached_videos: dict
    ) -> list:
        """
        按句子顺序合并生成的和缓存的视频路径
        
        Args:
            sentences: 所有句子列表（按顺序）
            generated_videos: 新生成的视频字典 {sentence_id: path}
            cached_videos: 缓存的视频字典 {sentence_id: path}
            
        Returns:
            按顺序排列的视频路径列表
        """
        video_paths = []
        
        for sentence in sentences:
            sentence_id = str(sentence.id)
            
            if sentence_id in generated_videos:
                video_paths.append(generated_videos[sentence_id])
            elif sentence_id in cached_videos:
                video_paths.append(cached_videos[sentence_id])
            else:
                logger.warning(f"⚠️ 句子 {sentence_id} 没有视频（跳过）")
        
        return video_paths

    async def synthesize_video(self, video_task_id: str) -> dict:
        """
        合成视频（主流程）

        Args:
            video_task_id: 视频任务ID

        Returns:
            统计信息字典
        """
        async with self:
            temp_dir = None
            try:
                # 检查FFmpeg
                if not check_ffmpeg_installed():
                    raise BusinessLogicError("FFmpeg未安装或不可用")

                # 1. 加载视频任务
                task_service = VideoTaskService(self.db_session)
                task = await task_service.get_video_task_by_id(video_task_id)

                # 2. 验证任务状态
                if task.status not in [VideoTaskStatus.PENDING.value, VideoTaskStatus.FAILED.value]:
                    raise BusinessLogicError(
                        f"任务状态不正确: {task.status}"
                    )

                # 3. 更新状态为验证中
                await task_service.update_task_status(task.id, VideoTaskStatus.VALIDATING)

                # 4. 加载章节并验证素材
                chapter_service = ChapterService(self.db_session)
                chapter = await chapter_service.get_chapter_by_id(task.chapter_id)
                await self._validate_chapter_materials(chapter)

                # 5. 解析生成设置
                gen_setting = task.get_gen_setting()

                # 6. 如果任务包含api_key_id，加载API密钥用于LLM纠错
                api_key = None
                model = None
                if task.api_key_id:
                    try:
                        api_key_service = APIKeyService(self.db_session)
                        api_key = await api_key_service.get_api_key_by_id(
                            str(task.api_key_id),
                            str(task.user_id)
                        )
                        logger.info(f"[LLM纠错] 已加载API密钥，将使用LLM纠正字幕")
                        
                        # 可以从gen_setting中获取模型配置
                        model = gen_setting.get("llm_model")
                    except Exception as e:
                        logger.warning(f"加载API密钥失败，将不使用LLM纠错: {e}")
                        api_key = None

                # 7. 更新状态为下载素材
                await task_service.update_task_status(task.id, VideoTaskStatus.DOWNLOADING_MATERIALS)

                # 8. 获取所有句子
                sentences = await chapter_service.get_sentences(task.chapter_id)
                task.total_sentences = len(sentences)
                await self.db_session.flush()

                # 9. 创建临时目录
                temp_dir = Path(tempfile.mkdtemp(prefix="video_synthesis_"))
                logger.info(f"创建临时目录: {temp_dir}")

                # 10. 更新状态为合成视频
                await task_service.update_task_status(
                    task.id,
                    VideoTaskStatus.SYNTHESIZING_VIDEOS
                )

                # 11. 分类句子：需要生成 vs 可以复用缓存
                sentences_to_generate = []
                cached_sentences = []
                
                for sentence in sentences:
                    if sentence.has_valid_cache():
                        cached_sentences.append(sentence)
                        logger.info(f"🔄 句子 {sentence.order_index} 使用缓存: {sentence.sentence_video_key}")
                    else:
                        sentences_to_generate.append(sentence)
                        logger.info(f"🆕 句子 {sentence.order_index} 需要重新生成")
                
                logger.info(
                    f"📊 缓存统计: 总计 {len(sentences)} 个句子, "
                    f"复用缓存 {len(cached_sentences)} 个, "
                    f"需要生成 {len(sentences_to_generate)} 个"
                )

                # 12. 并发生成需要更新的句子视频
                generated_videos = {}
                if sentences_to_generate:
                    semaphore = asyncio.Semaphore(3)  # 限制并发数为3
                    tasks_list = [
                        self._process_sentence_with_cache(
                            sentence, temp_dir, idx, gen_setting, semaphore, str(task.user_id), api_key, model
                        )
                        for idx, sentence in enumerate(sentences_to_generate)
                    ]
                    
                    results = await asyncio.gather(*tasks_list, return_exceptions=True)
                    
                    # 收集成功生成的视频
                    for idx, (success, video_path, error) in enumerate(results):
                        if success and video_path:
                            sentence_id = str(sentences_to_generate[idx].id)
                            generated_videos[sentence_id] = video_path
                        elif error:
                            logger.error(f"句子 {idx} 生成失败: {error}")
                
                # 13. 下载缓存的句子视频
                cached_videos = {}
                if cached_sentences:
                    for sentence in cached_sentences:
                        try:
                            video_path = await self._download_cached_video(sentence, temp_dir)
                            cached_videos[str(sentence.id)] = video_path
                        except Exception as e:
                            logger.error(f"下载缓存视频失败 {sentence.id}: {e}")
                            # 如果缓存下载失败，标记需要重新生成
                            sentence.mark_material_updated()
                            await self.db_session.flush()
                
                # 14. 合并所有视频路径（按句子顺序）
                video_paths = self._merge_video_paths(
                    sentences,
                    generated_videos,
                    cached_videos
                )
                
                if not video_paths:
                    raise BusinessLogicError("没有可用的视频文件")
                
                logger.info(f"📹 共收集到 {len(video_paths)} 个视频文件")

                # 15. 统计结果
                success_count = len(generated_videos) + len(cached_videos)
                failed_count = len(sentences) - success_count
                
                logger.info(f"✅ 成功: {success_count}, ❌ 失败: {failed_count}")
                
                # 16. 更新API密钥使用统计（如果使用了LLM纠错）
                if api_key:
                    try:
                        api_key_service = APIKeyService(self.db_session)
                        # 每个句子调用一次LLM，所以使用次数为句子数量
                        for _ in range(len(sentences)):
                            await api_key_service.update_usage(api_key.id, str(task.user_id))
                        logger.info(f"[LLM纠错] 已更新API密钥使用统计，共 {len(sentences)} 次")
                    except Exception as e:
                        logger.warning(f"更新API密钥使用统计失败: {e}")

                # 17. 更新状态为拼接中
                await task_service.update_task_status(task.id, VideoTaskStatus.CONCATENATING)
                task.update_progress(85)
                await self.db_session.flush()

                # 15. 拼接视频
                final_video_path = temp_dir / "final_video.mp4"
                concat_file_path = temp_dir / "concat.txt"

                success = concatenate_videos(video_paths, final_video_path, concat_file_path)
                if not success:
                    raise BusinessLogicError("视频拼接失败")

                # 16. 更新状态为上传中
                await task_service.update_task_status(task.id, VideoTaskStatus.UPLOADING)
                task.update_progress(90)
                await self.db_session.flush()

                # 17. 上传到MinIO
                storage = await self._get_storage_client()
                video_key = storage.generate_object_key(
                    str(task.user_id),
                    f"chapter_{task.chapter_id}_video.mp4",
                    prefix="videos"
                )

                # 读取文件并上传
                from fastapi import UploadFile
                with open(final_video_path, 'rb') as f:
                    upload_file = UploadFile(
                        filename=f"chapter_{task.chapter_id}_video.mp4",
                        file=f
                    )
                    result = await storage.upload_file(
                        str(task.user_id),
                        upload_file,
                        object_key=video_key
                    )

                video_key = result["object_key"]

                # 18. 获取视频时长
                duration = int(get_audio_duration(str(final_video_path)) or 0)

                # 19. 标记任务完成
                await task_service.mark_task_completed(task.id, video_key, duration)
                task.update_progress(100)
                await self.db_session.flush()

                logger.info(f"视频合成完成: task_id={task.id}, video_key={video_key}")

                return {
                    "total": len(sentences),
                    "success": success_count,
                    "failed": failed_count,
                    "video_key": video_key,
                    "duration": duration
                }

            except Exception as e:
                logger.error(f"视频合成失败: {e}", exc_info=True)

                # 标记任务失败
                try:
                    task_service = VideoTaskService(self.db_session)
                    await task_service.mark_task_failed(
                        video_task_id,
                        str(e)
                    )
                except Exception as mark_error:
                    logger.error(f"标记任务失败时出错: {mark_error}")

                raise

            finally:
                # 清理临时目录
                if temp_dir and temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        logger.info(f"清理临时目录: {temp_dir}")
                    except Exception as e:
                        logger.error(f"清理临时目录失败: {e}")


# 创建全局实例
video_synthesis_service = VideoSynthesisService()

__all__ = [
    "VideoSynthesisService",
    "video_synthesis_service",
]
