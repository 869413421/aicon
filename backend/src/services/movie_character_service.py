"""
电影角色服务 - 负责角色提取、视觉特征建模、对话风格设计
"""

import json
import re
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.logging import get_logger
from src.models.movie import MovieCharacter, MovieScript, MovieScene, MovieShot
from src.services.base import BaseService
from src.services.provider.factory import ProviderFactory
from src.services.api_key import APIKeyService
from src.services.image import retry_with_backoff
from src.utils.storage import get_storage_client
import uuid
import io
import aiohttp
from fastapi import UploadFile

logger = get_logger(__name__)

class CharacterThreeViewPromptBuilder:
    """
    角色三视图提示词生成器
    根据 Gemini 3 Pro Image 最佳实践生成提示词
    核心结构: [时代背景] + [角色身份] + [三视图要求] + [一致性关键词] + [风格/技术参数]
    """
    
    TEMPLATE = """LIVE-ACTION CINEMATIC CHARACTER REFERENCE featuring THREE CONSISTENT PHOTOGRAPHED VIEWS of the SAME REAL HUMAN ACTOR portraying {name}:
front view, 90-degree profile view, and back view.

**THIS IS NOT A 3D RENDER. THIS IS NOT CGI. THIS IS NOT ANIMATION.**
This is a live-action, real human actor photographed for a feature film character reference.

Character details:
- Name: {name}
- Era / Setting: {era_background}
- Role: {occupation}
- Appearance: {key_visual_traits}

Actor & Consistency Requirements:
- The SAME real human actor appears in all three views
- Identical facial structure, skin texture, pores, scars, and micro-details
- Identical hairstyle, hairline, hair length, and hair color
- Identical costume, wear marks, fabric folds, and equipment placement
- Natural human posture, neutral production stance
- Emotionless or neutral expression suitable for film reference photography

Live-Action Photography & Cinematography:
- Shot as live-action film stills
- Feature film quality
- Shot on ARRI ALEXA / RED cinema camera
- Professional cinematic lighting setup, soft but directional
- Realistic skin tones with natural imperfections (pores, fine lines, texture)
- Subtle film grain, cinematic contrast, realistic depth of field
- Neutral or dark studio background, similar to a movie costume test shoot
- NO 3D rendering artifacts, NO CGI smoothness, NO artificial perfection

Technical Output:
- Ultra-high detail live-action character reference
- Photorealistic human photography
- Aspect ratio: 16:9
"""
    
    @classmethod
    def build_prompt(
        cls,
        name: str,
        era_background: Optional[str] = None,
        occupation: Optional[str] = None,
        key_visual_traits: Optional[List[str]] = None,
        visual_traits: Optional[str] = None,
        role_description: Optional[str] = None
    ) -> str:
        """
        构建三视图提示词
        
        Args:
            name: 角色名称
            era_background: 时代背景 (如: "1940s WWII", "Victorian Era", "Cyberpunk 2077")
            occupation: 职业/社会地位
            key_visual_traits: 核心视觉特征列表 (3-4个)
            visual_traits: 详细视觉特征描述 (备用)
            role_description: 角色描述 (备用)
        
        Returns:
            生成的三视图提示词
        """
        # 使用默认值或从其他字段推断
        era = era_background or "Modern era"
        occ = occupation or "Unknown occupation"
        
        # 处理核心视觉特征
        if key_visual_traits and len(key_visual_traits) > 0:
            traits_str = ", ".join(key_visual_traits)
        elif visual_traits:
            # 如果没有key_visual_traits,从visual_traits中提取前100个字符作为简要描述
            traits_str = visual_traits[:100] + "..." if len(visual_traits) > 100 else visual_traits
        else:
            traits_str = "Standard appearance"
        
        # 生成提示词
        prompt = cls.TEMPLATE.format(
            name=name,
            era_background=era,
            occupation=occ,
            key_visual_traits=traits_str
        )
        
        return prompt

class MovieCharacterService(BaseService):
    """
    角色管理服务
    """

    EXTRACT_CHARACTERS_PROMPT = """
你是一个资深的选角导演。请分析以下电影剧本片段,提取出其中出现的所有主要角色。

### 输出要求:
必须以 JSON 格式输出,结构如下:
{{
  "characters": [
    {{
      "name": "角色姓名",
      "era_background": "时代背景(如: 1940s WWII, Victorian Era, Cyberpunk 2077, Modern era等)",
      "occupation": "职业或社会地位",
      "role_description": "角色的身份、背景、性格特点",
      "visual_traits": "详细的视觉特征描述(如:年龄、发色、发型、穿着、面部特征、体型),用于AI生图。",
      "key_visual_traits": ["核心视觉特征1", "核心视觉特征2", "核心视觉特征3"],
      "dialogue_traits": "角色的对话风格(如:冷静、粗鲁、幽默、书生气、口音特点等)"
    }}
  ]
}}

### 重要规则:
1. **角色名称一致性**: 
   - 同一角色必须使用完全相同的名称,不要有任何变化
   - 如果角色有中文名和英文名,统一使用"中文名 (英文名)"格式,例如: "阿尔德里克 (Aldric)"
   - 不要在同一个输出中出现"阿尔德里克"和"阿尔德里克 (Aldric)"这样的重复
   - 角色名称应该简洁明确,避免添加额外的描述性文字

2. **字段要求**:
   - era_background: 根据剧本内容推断时代背景,如果不明确则使用"Modern era"
   - occupation: 角色的职业或社会地位
   - key_visual_traits: 提取3-4个最关键的视觉特征,用于生成角色三视图

3. **特征提取要求**:
    - 优先从剧本中提取明确描述的视觉特征，如果剧本中没有明确描述，则根据角色的身份和时代背景进行合理推断
    - 对话风格应反映角色的性格和背景,例如:贵族角色可能说话较为正式,街头混混可能使用俚语
    - 尽可能详细的特征提取，则根据角色的身份和时代背景进行合理推断。
    

待分析剧本:
---
{text}
---
"""

    async def extract_characters_from_script(self, script_id: str, api_key_id: str, model: str = None) -> List[MovieCharacter]:
        """
        从剧本中提取角色
        """
        # 1. 加载剧本内容
        script = await self.db_session.get(MovieScript, script_id, options=[
            selectinload(MovieScript.scenes).selectinload(MovieScene.shots)
        ])
        if not script:
            raise ValueError("未找到剧本")
        
        # 拼凑剧本全文用于分析
        script_text = ""
        for scene in script.scenes:
            script_text += f"场景 {scene.order_index}: {scene.location} - {scene.description}\n"
            for shot in scene.shots:
                if shot.dialogue:
                    script_text += f"镜头 {shot.order_index} 对话: {shot.dialogue}\n"

        # 2. 加载 API Key
        from src.models.chapter import Chapter
        chapter = await self.db_session.get(Chapter, script.chapter_id, options=[selectinload(Chapter.project)])
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(chapter.project.owner_id))
        
        llm_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )

        try:
            prompt = self.EXTRACT_CHARACTERS_PROMPT.format(text=script_text[:5000]) # 限制长度
            response = await llm_provider.completions(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的选角导演JSON生成器。"},
                    {"role": "user", "content": prompt},
                ],
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            
            char_data = json.loads(content)
            
            # 获取项目中已存在的所有角色
            stmt = select(MovieCharacter).where(MovieCharacter.project_id == chapter.project_id)
            existing_result = await self.db_session.execute(stmt)
            existing_characters = {char.name: char for char in existing_result.scalars().all()}
            
            def normalize_name(name: str) -> str:
                """标准化角色名称,提取核心名称用于匹配"""
                # 移除括号及其内容,只保留主要名称
                core_name = re.sub(r'\s*\([^)]*\)', '', name).strip()
                return core_name
            
            def find_matching_character(char_name: str, existing_chars: dict) -> Optional[MovieCharacter]:
                """智能查找匹配的角色"""
                # 1. 精确匹配
                if char_name in existing_chars:
                    return existing_chars[char_name]
                
                # 2. 标准化名称匹配
                normalized_new = normalize_name(char_name)
                for existing_name, existing_char in existing_chars.items():
                    normalized_existing = normalize_name(existing_name)
                    if normalized_new == normalized_existing:
                        return existing_char
                
                return None
            
            created_characters = []
            for char in char_data.get("characters", []):
                char_name = char.get("name", "").strip()
                if not char_name:
                    continue
                
                # 智能查找已存在的角色
                existing_char = find_matching_character(char_name, existing_characters)
                
                # 生成三视图提示词
                generated_prompt = CharacterThreeViewPromptBuilder.build_prompt(
                    name=char_name,
                    era_background=char.get("era_background"),
                    occupation=char.get("occupation"),
                    key_visual_traits=char.get("key_visual_traits"),
                    visual_traits=char.get("visual_traits"),
                    role_description=char.get("role_description")
                )
                
                if existing_char:
                    # 更新已存在的角色
                    existing_char.role_description = char.get("role_description")
                    existing_char.visual_traits = char.get("visual_traits")
                    existing_char.dialogue_traits = char.get("dialogue_traits")
                    existing_char.era_background = char.get("era_background")
                    existing_char.occupation = char.get("occupation")
                    existing_char.key_visual_traits = char.get("key_visual_traits", [])
                    existing_char.generated_prompt = generated_prompt
                    created_characters.append(existing_char)
                else:
                    # 创建新角色
                    character = MovieCharacter(
                        project_id=chapter.project_id,
                        name=char_name,
                        role_description=char.get("role_description"),
                        visual_traits=char.get("visual_traits"),
                        dialogue_traits=char.get("dialogue_traits"),
                        era_background=char.get("era_background"),
                        occupation=char.get("occupation"),
                        key_visual_traits=char.get("key_visual_traits", []),
                        generated_prompt=generated_prompt
                    )
                    self.db_session.add(character)
                    existing_characters[char_name] = character  # 添加到已存在列表,避免本次提取中的重复
                    created_characters.append(character)
            
            await self.db_session.commit()
            return created_characters
            
        except Exception as e:
            logger.error(f"提取角色失败: {e}")
            raise
    
    async def generate_character_avatar(self, character_id: str, api_key_id: str, model: str = None, prompt: str = None, style: str = "cinematic") -> str:
        """
        生成角色头像/定妆照
        """
        char = await self.db_session.get(MovieCharacter, character_id)
        if not char:
            raise ValueError("未找到角色")
        
        # 加载 API Key
        from src.models.project import Project
        project = await self.db_session.get(Project, char.project_id)
        api_key_service = APIKeyService(self.db_session)
        api_key = await api_key_service.get_api_key_by_id(api_key_id, str(project.owner_id))

        image_provider = ProviderFactory.create(
            provider=api_key.provider,
            api_key=api_key.get_api_key(),
            base_url=api_key.base_url
        )
        
        try:
            # 直接使用前端传递的提示词(用户已微调过的三视图提示词)
            if not prompt:
                raise ValueError("必须提供生成提示词")
            
             # 增强提示词，让AI模型在图片左上角生成角色名称
            enhanced_prompt = f"{prompt}. IMPORTANT: Include the text '{char.name}' in the top-left corner of the image, clearly visible and readable."
            
            # 调用生图模型
            logger.info(f"生成角色头像提示词: {enhanced_prompt}")
            result = await retry_with_backoff(
                lambda: image_provider.generate_image(
                    prompt=enhanced_prompt,
                    model=model
                )
            )
            
            image_data = result.data[0]
            
            # 5. 处理图片数据 (支持两种返回格式)
            # 优先使用 b64_json (Gemini 新格式), 否则使用 url
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                # Gemini 返回 base64 数据
                import base64
                base64_data = image_data.b64_json
                mime_type = getattr(image_data, 'mime', 'image/png')
                
                logger.info(f"使用 b64_json 格式, MIME: {mime_type}, 数据长度: {len(base64_data)}")
                
                # 解码 base64
                image_bytes = base64.b64decode(base64_data)
            elif hasattr(image_data, 'url') and image_data.url:
                # 处理 URL 格式 (其他 Provider)
                import base64
                import re
                
                image_url = image_data.url
                logger.info(f"使用 url 格式, URL前50字符: {image_url[:50]}")
                
                if image_url.startswith("data:"):
                    # 解析 data URL: data:image/jpeg;base64,/9j/4AAQ...
                    match = re.match(r'data:([^;]+);base64,(.+)', image_url)
                    if not match:
                        raise ValueError(f"无效的 data URL 格式: {image_url[:100]}")
                    
                    mime_type = match.group(1)
                    base64_data = match.group(2)
                    image_bytes = base64.b64decode(base64_data)
                    logger.info(f"从 data URL 解码图片, MIME 类型: {mime_type}, 大小: {len(image_bytes)} bytes")
                else:
                    # 处理 HTTP URL (其他提供商)
                    async with aiohttp.ClientSession() as http_session:
                        async with http_session.get(image_url) as resp:
                            if resp.status != 200:
                                raise Exception(f"下载图片失败: {resp.status}")
                            image_bytes = await resp.read()
                            mime_type = resp.content_type or 'image/png'
                            logger.info(f"从 HTTP URL 下载图片, 大小: {len(image_bytes)} bytes")
            else:
                raise ValueError("图片生成失败: Provider 既没有返回 b64_json 也没有返回 url")
            
            # 6. 上传到 MinIO

            storage_client = await get_storage_client()
            file_id = str(uuid.uuid4())
            upload_file = UploadFile(
                filename=f"{file_id}.jpg",
                file=io.BytesIO(image_bytes),
            )
            
            storage_result = await storage_client.upload_file(
                user_id=str(project.owner_id),
                file=upload_file,
                metadata={"character_id": str(char.id)}
            )
            object_key = storage_result["object_key"]

            # 6. 更新角色信息
            char.avatar_url = object_key
            
            # 更新参考图列表
            refs = list(char.reference_images) if char.reference_images else []
            if object_key not in refs:
                refs.insert(0, object_key)
                char.reference_images = refs
            
            await self.db_session.commit()
            return object_key
            
        except Exception as e:
            logger.error(f"生成角色头像失败: {e}")
            raise

    async def batch_generate_avatars(self, project_id: str, api_key_id: str, model: str = None) -> dict:
        """
        批量生成角色定妆照
        使用并发请求提高效率
        """
        from sqlalchemy import select
        import asyncio
        
        # 获取所有未生成头像的角色
        stmt = select(MovieCharacter).where(
            MovieCharacter.project_id == project_id,
            MovieCharacter.avatar_url == None
        )
        result = await self.db_session.execute(stmt)
        characters = result.scalars().all()
        
        if not characters:
            return {"success": 0, "failed": 0, "total": 0, "message": "没有需要生成头像的角色"}
        
        logger.info(f"开始批量生成 {len(characters)} 个角色的定妆照")
        
        # 定义单个角色的生成任务
        async def generate_single(char):
            try:
                if not char.generated_prompt:
                    logger.warning(f"角色 {char.name} 没有generated_prompt,跳过")
                    return {"success": False, "character": char.name, "error": "缺少生成提示词"}
                
                await self.generate_character_avatar(
                    str(char.id),
                    api_key_id,
                    model,
                    char.generated_prompt,
                    "cinematic"
                )
                logger.info(f"成功生成角色 {char.name} 的头像")
                return {"success": True, "character": char.name}
            except Exception as e:
                logger.error(f"生成角色 {char.name} 头像失败: {e}")
                return {"success": False, "character": char.name, "error": str(e)}
        
        # 并发执行所有生成任务
        results = await asyncio.gather(*[generate_single(char) for char in characters], return_exceptions=True)
        
        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed_count = len(results) - success_count
        
        logger.info(f"批量生成完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(characters),
            "details": results
        }

__all__ = ["MovieCharacterService"]

if __name__ == "__main__":
    
    # 测试代码
    import asyncio
    
    prompt = """
    TRIPLE-VIEW CHARACTER SHEET: front, 90° side, back views of cyberpunk hacker "Kitsune", year 2089.

Details:
- Japanese female, 22, augmented with neon cyan neural ports behind ears
- Outfit: asymmetrical leather jacket, holographic crop top, cargo pants with utility straps
- Hair: short silver bob with glowing pink streaks
- Accessories: AR glasses, data-glove on right hand, katana sheath on back

CONSISTENCY LOCK:
- Same port positions and glow intensity
- Jacket pattern must align perfectly
- Hair length and streak position identical
- Glasses frame style consistent

Render: Unreal Engine 5, photorealistic, studio lighting, black background. --ar 16:9
    """
    
    # 测试角色头像生成
    async def test_generate_avatar():
        from src.core.database import get_async_db
        async with get_async_db() as session:
            service = MovieCharacterService(session)
            url = await service.generate_character_avatar(
                character_id="8341a465-d0ae-4c77-93d9-e0d799de1568",
                api_key_id="457f4337-8f54-4749-a2d6-78e1febf9028",
                model="gemini-3-pro-image-preview",
                # prompt="Cinematic lighting, movie still, 8k, photorealistic, dramatic, highly detailed face, 赛博朋克世界观下,男性，约35岁，眼神深邃且带着长期的疲惫。面部有轻微的擦伤。身着深灰色战术外骨骼装甲，带有明显的战斗损耗痕迹。短发凌乱，体型健硕但并不夸张，展现出敏捷与力量感。",
                prompt=prompt,
                style="cinematic"
            )
            print("Generated Avatar URL:", url)
    asyncio.run(test_generate_avatar())