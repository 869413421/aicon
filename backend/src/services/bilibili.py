"""
Bilibili发布服务
"""

import asyncio
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

from sqlalchemy import select

from src.core.logging import get_logger
from src.core.config import settings
from src.services.base import BaseService, SessionManagedService

logger = get_logger(__name__)


class BilibiliService(BaseService):
    """B站发布服务 - 基础CLI交互"""
    
    def __init__(self, db_session=None):
        super().__init__(db_session)
        self.biliup_path = self._get_biliup_path()
        self.cookie_dir = Path("./data/bilibili_cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_biliup_path(self) -> str:
        """获取biliup可执行文件路径"""
        import platform
        if platform.system() == "Windows":
            return str(Path("./bin/biliup.exe").absolute())
        return str(Path("./bin/biliup").absolute())
    
    async def login_by_qrcode(self, account_id: str) -> Dict[str, Any]:
        """
        二维码登录
        
        Args:
            account_id: 账号ID
            
        Returns:
            登录结果
        """
        cookie_file = self.cookie_dir / f"{account_id}.json"
        
        cmd = [
            self.biliup_path,
            "login",
            "--cookie-file", str(cookie_file)
        ]
        
        logger.info(f"执行登录命令: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"账号 {account_id} 登录成功")
                return {
                    "success": True,
                    "cookie_file": str(cookie_file),
                    "message": "登录成功"
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"账号 {account_id} 登录失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
        except Exception as e:
            logger.error(f"登录过程异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        desc: str = "",
        tid: int = 171,
        cover: Optional[str] = None,
        tag: Optional[str] = None,
        copyright: int = 1,
        source: Optional[str] = None,
        dynamic: Optional[str] = None,
        dtime: Optional[int] = None,
        cookie_file: Optional[str] = None,
        line: str = "kodo",
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        上传视频到B站
        
        Args:
            video_path: 视频文件路径
            title: 视频标题
            desc: 视频简介
            tid: 投稿分区
            cover: 封面图片路径
            tag: 标签,逗号分隔
            copyright: 1原创 2转载
            source: 转载来源
            dynamic: 空间动态
            dtime: 延时发布时间戳
            cookie_file: cookie文件路径
            line: 上传线路
            limit: 并发数
            
        Returns:
            上传结果
        """
        cmd = [
            self.biliup_path,
            "upload",
            video_path,
            "--title", title,
            "--desc", desc,
            "--tid", str(tid),
            "--copyright", str(copyright),
            "--line", line,
            "--limit", str(limit)
        ]
        
        if cover:
            cmd.extend(["--cover", cover])
        if tag:
            cmd.extend(["--tag", tag])
        if source:
            cmd.extend(["--source", source])
        if dynamic:
            cmd.extend(["--dynamic", dynamic])
        if dtime:
            cmd.extend(["--dtime", str(dtime)])
        if cookie_file:
            cmd.extend(["--cookie-file", cookie_file])
        
        logger.info(f"执行上传命令: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                logger.info(f"上传成功: {output}")
                
                # 提取BV号
                bvid = self._extract_bvid(output)
                aid = self._extract_aid(output)
                
                return {
                    "success": True,
                    "bvid": bvid,
                    "aid": aid,
                    "output": output
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"上传失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
        except Exception as e:
            logger.error(f"上传过程异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_bvid(self, output: str) -> Optional[str]:
        """从输出中提取BV号"""
        match = re.search(r'BV[a-zA-Z0-9]+', output)
        return match.group(0) if match else None
    
    def _extract_aid(self, output: str) -> Optional[str]:
        """从输出中提取AV号"""
        match = re.search(r'av(\d+)', output, re.IGNORECASE)
        return match.group(1) if match else None
    
    async def get_cookie_file(self, user_id: str) -> Optional[str]:
        """
        获取用户的cookie文件路径
        
        Args:
            user_id: 用户ID
            
        Returns:
            cookie文件路径,如果不存在返回None
        """
        from src.models.publish_task import BilibiliAccount
        
        query = select(BilibiliAccount).where(
            BilibiliAccount.user_id == user_id,
            BilibiliAccount.is_active == True
        ).order_by(BilibiliAccount.last_login_at.desc())
        
        result = await self.execute(query)
        account = result.scalar_one_or_none()
        
        if account and account.cookie_path:
            cookie_path = Path(account.cookie_path)
            if cookie_path.exists():
                return str(cookie_path)
        
        return None


class BilibiliPublishService(SessionManagedService):
    """
    Bilibili发布服务 - 管理发布任务业务逻辑
    
    核心功能:
    1. 发布任务流程管理 - 从视频下载到上传的完整流程
    2. 状态跟踪管理 - 实时进度更新和错误处理
    3. 临时文件管理 - 下载、清理临时文件
    
    设计特点:
    - 会话自管理: 使用SessionManagedService独立管理数据库会话
    - 异步优先: 所有操作都是异步的
    - 容错设计: 完善的错误处理和恢复机制
    """
    
    def __init__(self):
        super().__init__()
        self._bilibili_service = None
        self._storage_service = None
    
    async def _get_bilibili_service(self):
        """延迟导入bilibili_service"""
        if self._bilibili_service is None:
            self._bilibili_service = BilibiliService(self.db_session)
        return self._bilibili_service
    
    async def _get_storage_service(self):
        """延迟导入storage_service"""
        if self._storage_service is None:
            from src.services.storage import storage_service
            self._storage_service = storage_service
        return self._storage_service
    
    async def upload_chapter_task(
        self,
        publish_task_id: str,
        user_id: str,
        celery_task_id: str
    ) -> Dict[str, Any]:
        """
        上传章节视频到B站的完整任务流程
        
        专门为Celery任务调用设计,提供完整的异常处理和状态管理。
        
        Args:
            publish_task_id: 发布任务ID
            user_id: 用户ID
            celery_task_id: Celery任务ID
            
        Returns:
            上传结果
        """
        from src.models.publish_task import PublishTask
        from src.services.chapter import ChapterService
        
        try:
            logger.info(f"开始Bilibili上传任务: publish_task_id={publish_task_id}")
            
            # 1. 获取发布任务
            query = select(PublishTask).where(PublishTask.id == publish_task_id)
            result = await self.execute(query)
            publish_task = result.scalar_one_or_none()
            
            if not publish_task:
                raise ValueError(f"发布任务不存在: {publish_task_id}")
            
            # 2. 标记为上传中
            publish_task.mark_as_uploading()
            publish_task.celery_task_id = celery_task_id
            await self.commit()
            
            # 3. 获取章节信息
            chapter_service = ChapterService(self.db_session)
            chapter = await chapter_service.get_chapter_by_id(
                str(publish_task.chapter_id)
            )
            
            if not chapter or not chapter.video_url:
                raise ValueError("章节视频未生成")
            
            logger.info(f"开始上传章节 {chapter.id} 到B站")
            
            # 4. 下载视频和封面
            video_path = await self._download_video(chapter.video_url)
            cover_path = None
            if publish_task.cover_url:
                cover_path = await self._download_cover(publish_task.cover_url)
            
            # 5. 获取cookie文件
            bilibili_service = await self._get_bilibili_service()
            cookie_file = await bilibili_service.get_cookie_file(user_id)
            
            if not cookie_file:
                raise ValueError("未找到B站登录凭证,请先登录")
            
            # 6. 上传到B站
            upload_result = await bilibili_service.upload_video(
                video_path=video_path,
                title=publish_task.title,
                desc=publish_task.desc or "",
                tid=publish_task.tid,
                cover=cover_path,
                tag=publish_task.tag,
                copyright=publish_task.copyright,
                source=publish_task.source,
                dynamic=publish_task.dynamic,
                dtime=publish_task.dtime,
                cookie_file=cookie_file,
                line=publish_task.upload_line,
                limit=publish_task.upload_limit
            )
            
            # 7. 清理临时文件
            self._cleanup_temp_file(video_path)
            if cover_path:
                self._cleanup_temp_file(cover_path)
            
            # 8. 更新任务状态
            if upload_result["success"]:
                publish_task.mark_as_published(
                    bvid=upload_result.get("bvid"),
                    aid=upload_result.get("aid")
                )
                logger.info(f"章节 {chapter.id} 上传成功: BV{upload_result.get('bvid')}")
            else:
                publish_task.mark_as_failed(upload_result.get("error", "未知错误"))
                logger.error(f"章节 {chapter.id} 上传失败: {upload_result.get('error')}")
            
            await self.commit()
            
            return {
                "success": upload_result["success"],
                "bvid": upload_result.get("bvid"),
                "aid": upload_result.get("aid"),
                "error": upload_result.get("error")
            }
            
        except Exception as e:
            logger.error(f"上传任务异常: {e}", exc_info=True)
            
            # 标记任务失败
            if publish_task:
                publish_task.mark_as_failed(str(e))
                await self.commit()
            
            raise
    
    async def _download_video(self, video_url: str) -> str:
        """下载视频到临时文件"""
        storage_service = await self._get_storage_service()
        
        # 创建临时文件
        temp_dir = Path(tempfile.gettempdir()) / "biliup_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = temp_dir / f"video_{os.urandom(8).hex()}.mp4"
        
        # 下载视频
        await storage_service.download_file(video_url, str(temp_file))
        
        logger.info(f"视频已下载到: {temp_file}")
        return str(temp_file)
    
    async def _download_cover(self, cover_url: str) -> str:
        """下载封面到临时文件"""
        storage_service = await self._get_storage_service()
        
        temp_dir = Path(tempfile.gettempdir()) / "biliup_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据URL确定文件扩展名
        ext = Path(cover_url).suffix or ".jpg"
        temp_file = temp_dir / f"cover_{os.urandom(8).hex()}{ext}"
        
        # 下载封面
        await storage_service.download_file(cover_url, str(temp_file))
        
        logger.info(f"封面已下载到: {temp_file}")
        return str(temp_file)
    
    def _cleanup_temp_file(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"已清理临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")


# 全局实例
bilibili_publish_service = BilibiliPublishService()

__all__ = [
    "BilibiliService",
    "BilibiliPublishService",
    "bilibili_publish_service",
]
