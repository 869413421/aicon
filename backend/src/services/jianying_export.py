"""
剪映导出服务 - 将章节素材导出为剪映草稿格式
"""

import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.chapter import Chapter, ChapterStatus
from src.models.sentence import Sentence
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class JianYingExportError(Exception):
    """剪映导出异常"""
    pass


class JianYingExportService:
    """剪映导出服务"""
    
    # 默认画布配置 (16:9)
    DEFAULT_CANVAS = {
        "width": 1920,
        "height": 1080,
        "ratio": "16:9"
    }
    
    # 时间单位转换: 秒 -> 微秒
    SECOND_TO_MICROSECOND = 1_000_000
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def export_chapter(
        self,
        chapter_id: str,
        user_id: str
    ) -> str:
        """
        导出章节为剪映草稿格式
        
        Args:
            chapter_id: 章节ID
            user_id: 用户ID
            
        Returns:
            导出的ZIP文件路径
            
        Raises:
            JianYingExportError: 导出失败
        """
        try:
            # 1. 获取章节和句子数据
            chapter, sentences = await self._get_chapter_data(chapter_id, user_id)
            
            # 2. 验证章节状态
            if chapter.status != ChapterStatus.MATERIALS_PREPARED.value:
                raise JianYingExportError(
                    f"章节状态不正确，当前状态: {chapter.status}，需要: {ChapterStatus.MATERIALS_PREPARED.value}"
                )
            
            # 3. 创建临时工作目录 - 使用系统临时目录以便文件在请求间持久化
            temp_base_dir = Path(tempfile.gettempdir())
            draft_dir = temp_base_dir / f"jianying_export_{uuid.uuid4().hex[:8]}" / f"draft_{uuid.uuid4().hex[:8]}"
            draft_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # 4. 下载素材文件
                materials_info = await self._download_materials(sentences, draft_dir)
                
                # 5. 生成 draft_content.json
                draft_content = self._generate_draft_content(
                    chapter, sentences, materials_info
                )
                draft_content_path = draft_dir / "draft_content.json"
                with open(draft_content_path, 'w', encoding='utf-8') as f:
                    json.dump(draft_content, f, ensure_ascii=False, indent=2)
                
                # 6. 生成 draft_meta_info.json
                draft_meta = self._generate_draft_meta_info(
                    chapter, draft_content["duration"]
                )
                draft_meta_path = draft_dir / "draft_meta_info.json"
                with open(draft_meta_path, 'w', encoding='utf-8') as f:
                    json.dump(draft_meta, f, ensure_ascii=False, indent=2)
                
                # 7. 打包为 ZIP - 保存到系统临时目录
                zip_path = await self._create_zip_package(
                    draft_dir, chapter, str(temp_base_dir)
                )
                
                logger.info(f"章节 {chapter_id} 导出成功: {zip_path}")
                return zip_path
                
            finally:
                # 清理临时目录（保留ZIP文件）- 清理整个导出目录
                export_dir = draft_dir.parent
                if export_dir.exists() and export_dir.name.startswith("jianying_export_"):
                    shutil.rmtree(export_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.error(f"导出章节失败: {e}", exc_info=True)
            raise JianYingExportError(f"导出失败: {str(e)}")
    
    async def _get_chapter_data(
        self, chapter_id: str, user_id: str
    ) -> tuple[Chapter, List[Sentence]]:
        """获取章节和句子数据"""
        from src.models.project import Project
        
        # 获取章节（通过project检查权限）
        query = select(Chapter).join(Project).where(
            Chapter.id == chapter_id,
            Project.owner_id == user_id
        )
        result = await self.db.execute(query)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise JianYingExportError("章节不存在或无权访问")
        
        # 获取句子列表（通过paragraph关联）
        from src.models.paragraph import Paragraph
        
        query = select(Sentence).join(Paragraph).where(
            Paragraph.chapter_id == chapter_id
        ).order_by(Paragraph.order_index, Sentence.order_index)
        result = await self.db.execute(query)
        sentences = result.scalars().all()
        
        if not sentences:
            raise JianYingExportError("章节没有句子数据")
        
        return chapter, list(sentences)
    
    async def _download_materials(
        self, sentences: List[Sentence], draft_dir: Path
    ) -> Dict[str, Dict[str, Any]]:
        """
        下载素材文件到本地
        
        Returns:
            materials_info: {sentence_id: {image_path, audio_path, ...}}
        """
        storage_client = await get_storage_client()
        materials_info = {}
        
        # 创建素材目录
        images_dir = draft_dir / "draft_materials" / "images"
        audios_dir = draft_dir / "draft_materials" / "audios"
        images_dir.mkdir(parents=True, exist_ok=True)
        audios_dir.mkdir(parents=True, exist_ok=True)
        
        for sentence in sentences:
            sentence_materials = {}
            
            # 下载图片
            if sentence.image_url:
                image_filename = f"{sentence.id}.jpg"
                image_path = images_dir / image_filename
                try:
                    await storage_client.download_file_to_path(
                        sentence.image_url, str(image_path)
                    )
                    sentence_materials["image_path"] = f"draft_materials/images/{image_filename}"
                    sentence_materials["image_width"] = 1920  # 默认值
                    sentence_materials["image_height"] = 1080
                except Exception as e:
                    logger.warning(f"下载图片失败 {sentence.id}: {e}")
            
            # 下载音频
            if sentence.audio_url:
                audio_filename = f"{sentence.id}.mp3"
                audio_path = audios_dir / audio_filename
                try:
                    await storage_client.download_file_to_path(
                        sentence.audio_url, str(audio_path)
                    )
                    sentence_materials["audio_path"] = f"draft_materials/audios/{audio_filename}"
                    # 音频时长（微秒）
                    sentence_materials["audio_duration"] = int(
                        (sentence.audio_duration or 3.0) * self.SECOND_TO_MICROSECOND
                    )
                except Exception as e:
                    logger.warning(f"下载音频失败 {sentence.id}: {e}")
            
            materials_info[str(sentence.id)] = sentence_materials
        
        return materials_info
    
    def _generate_draft_content(
        self,
        chapter: Chapter,
        sentences: List[Sentence],
        materials_info: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成 draft_content.json 内容"""
        draft_id = uuid.uuid4().hex
        current_time = int(datetime.now().timestamp() * 1000)
        
        # 构建素材列表
        images_materials = []
        audios_materials = []
        
        for sentence in sentences:
            sentence_id = str(sentence.id)
            materials = materials_info.get(sentence_id, {})
            
            # 图片素材
            if "image_path" in materials:
                images_materials.append({
                    "id": f"image_{sentence_id}",
                    "path": materials["image_path"],
                    "duration": materials.get("audio_duration", 3 * self.SECOND_TO_MICROSECOND),
                    "width": materials.get("image_width", 1920),
                    "height": materials.get("image_height", 1080),
                    "type": "photo"
                })
            
            # 音频素材
            if "audio_path" in materials:
                audios_materials.append({
                    "id": f"audio_{sentence_id}",
                    "path": materials["audio_path"],
                    "duration": materials.get("audio_duration", 3 * self.SECOND_TO_MICROSECOND),
                    "type": "audio"
                })
        
        # 构建视频轨道（图片序列）
        video_segments = []
        current_time_offset = 0
        
        for sentence in sentences:
            sentence_id = str(sentence.id)
            materials = materials_info.get(sentence_id, {})
            
            if "image_path" in materials:
                duration = materials.get("audio_duration", 3 * self.SECOND_TO_MICROSECOND)
                video_segments.append({
                    "id": f"segment_video_{sentence_id}",
                    "material_id": f"image_{sentence_id}",
                    "target_timerange": {
                        "start": current_time_offset,
                        "duration": duration
                    },
                    "source_timerange": {
                        "start": 0,
                        "duration": duration
                    }
                })
                current_time_offset += duration
        
        # 构建音频轨道
        audio_segments = []
        current_time_offset = 0
        
        for sentence in sentences:
            sentence_id = str(sentence.id)
            materials = materials_info.get(sentence_id, {})
            
            if "audio_path" in materials:
                duration = materials.get("audio_duration", 3 * self.SECOND_TO_MICROSECOND)
                audio_segments.append({
                    "id": f"segment_audio_{sentence_id}",
                    "material_id": f"audio_{sentence_id}",
                    "target_timerange": {
                        "start": current_time_offset,
                        "duration": duration
                    },
                    "source_timerange": {
                        "start": 0,
                        "duration": duration
                    },
                    "volume": 1.0
                })
                current_time_offset += duration
        
        # 总时长
        total_duration = current_time_offset
        
        return {
            "version": "5.9.0",
            "draft_id": draft_id,
            "draft_name": chapter.title,
            "create_time": current_time,
            "update_time": current_time,
            "duration": total_duration,
            "materials": {
                "images": images_materials,
                "audios": audios_materials
            },
            "tracks": [
                {
                    "type": "video",
                    "segments": video_segments
                },
                {
                    "type": "audio",
                    "segments": audio_segments
                }
            ],
            "canvas_config": self.DEFAULT_CANVAS
        }
    
    def _generate_draft_meta_info(
        self, chapter: Chapter, duration: int
    ) -> Dict[str, Any]:
        """生成 draft_meta_info.json 内容"""
        draft_id = uuid.uuid4().hex
        current_time = int(datetime.now().timestamp() * 1000)
        
        return {
            "draft_id": draft_id,
            "draft_name": chapter.title,
            "draft_cover": "",
            "create_time": current_time,
            "update_time": current_time,
            "duration": duration,
            "canvas_config": self.DEFAULT_CANVAS
        }
    
    async def _create_zip_package(
        self, draft_dir: Path, chapter: Chapter, temp_dir: str
    ) -> str:
        """创建 ZIP 压缩包"""
        import zipfile
        
        # 生成文件名
        safe_title = "".join(
            c for c in chapter.title if c.isalnum() or c in (' ', '-', '_')
        ).strip()
        if not safe_title:  # 如果标题全是特殊字符
            safe_title = "chapter"
        zip_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.zip"
        zip_path = Path(temp_dir) / zip_filename
        
        # 打包 - 使用draft_dir作为根目录
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in draft_dir.rglob('*'):
                if file_path.is_file():
                    # 保持draft_xxx文件夹结构
                    arcname = file_path.relative_to(draft_dir.parent)
                    zipf.write(file_path, arcname)
                    logger.debug(f"添加文件到ZIP: {arcname}")
        
        file_size = zip_path.stat().st_size
        logger.info(f"创建ZIP包: {zip_path}, 大小: {file_size} bytes")
        
        if file_size < 100:  # 如果文件太小，可能有问题
            logger.warning(f"ZIP文件大小异常: {file_size} bytes")
        
        return str(zip_path)


__all__ = ["JianYingExportService", "JianYingExportError"]
