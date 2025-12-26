"""
关键帧生成提示词构建器
"""
from typing import List, Optional
from src.models.movie import MovieShot, MovieScene, MovieCharacter


class KeyframePromptBuilder:
    """
    关键帧生成提示词构建器
    强调真人电影风格，避免3D/CGI效果
    """
    
    # 核心风格指令 - 强调真人摄影
    CORE_STYLE = """
CRITICAL STYLE REQUIREMENTS:
- This MUST be a LIVE-ACTION PHOTOGRAPH, not 3D render, not CGI, not animation
- Real human actors in real physical locations
- Captured with professional cinema cameras (ARRI, RED, Sony Venice)
- Natural lighting and practical effects only
- Photorealistic skin texture, fabric detail, environmental elements
- Film grain and depth of field characteristic of cinema photography

CINEMATOGRAPHY FOR VIDEO ANIMATION:
- Composition should support camera movement (medium shots, two-shots work well)
- Include depth layers for natural parallax when animated
- Avoid extreme angles that limit transition possibilities
- Frame with spatial context (not too tight) to allow camera adjustments
- Establishing shots should show clear spatial relationships
"""

    # 技术规格
    TECHNICAL_SPECS = """
Technical Specifications:
- Shot on 35mm film or high-end digital cinema camera
- Cinematic color grading (film look, not digital/game look)
- Professional cinematography with intentional composition
- Natural depth of field and bokeh
- Realistic lighting (practical lights, natural light, or professional film lighting)

Video-Ready Composition (This frame will be animated):
- Clear subject with good spatial positioning for camera movement
- Depth layers (foreground/midground/background) to enable parallax effects
- Composition that allows for natural camera transitions (push in, pull back, pan)
- Action potential: subject positioned to suggest movement or interaction
- Avoid extreme close-ups that limit animation possibilities
- Frame with breathing room for camera adjustments
"""

    # 禁止的元素
    FORBIDDEN_ELEMENTS = """
ABSOLUTELY FORBIDDEN:
- NO 3D rendering artifacts
- NO CGI character models
- NO video game aesthetics
- NO anime or cartoon styles
- NO artificial/synthetic looking imagery
- NO obvious digital manipulation
"""
    
    # 无人物场景的禁止元素（更强调排除人物）
    NO_PEOPLE_FORBIDDEN_ELEMENTS = """
ABSOLUTELY FORBIDDEN:
- NO 3D rendering artifacts
- NO CGI character models
- NO video game aesthetics
- NO anime or cartoon styles
- NO artificial/synthetic looking imagery
- NO obvious digital manipulation
- NO people, human figures, characters, or persons of any kind
- NO men, women, children, or human silhouettes
- NO faces, bodies, or human body parts
- NO shadows or reflections of people
- NO crowds, groups, or individuals
- NO human presence, portraits, or human-like shapes
- NO mannequins or human-shaped objects
"""

    @staticmethod
    def build_prompt(
        shot: MovieShot,
        scene: MovieScene,
        characters: List[MovieCharacter],
        custom_prompt: Optional[str] = None,
        previous_shot: Optional[MovieShot] = None
    ) -> str:
        """
        构建关键帧生成提示词
        
        Args:
            shot: 分镜对象
            scene: 场景对象
            characters: 角色列表
            custom_prompt: 自定义提示词（如果提供则直接使用）
            previous_shot: 上一个分镜对象（用于保持视觉连续性）
            
        Returns:
            完整的提示词
        """
        if custom_prompt:
            # 自定义提示词仍然添加风格约束和视频就绪指导
            return f"""{custom_prompt}

{KeyframePromptBuilder.CORE_STYLE}

{KeyframePromptBuilder.TECHNICAL_SPECS}"""
        
        # 1. 场景上下文
        scene_context = KeyframePromptBuilder._build_scene_context(scene)
        
        # 2. 上一帧上下文（用于视觉连续性）
        previous_shot_context = KeyframePromptBuilder._build_previous_shot_context(previous_shot)
        
        # 3. 分镜描述
        shot_description = shot.shot or "A cinematic shot"
        
        # 4. 角色信息
        character_context = KeyframePromptBuilder._build_character_context(shot, characters)
        
        # 5. 对白提示（如果有）
        dialogue_hint = ""
        if shot.dialogue:
            dialogue_hint = f"\nDialogue context: {shot.dialogue[:100]}"
        
        # 6. 选择合适的禁止元素列表
        # 如果分镜不包含人物，使用更严格的禁止列表
        has_characters = shot.characters and len(shot.characters) > 0
        forbidden_elements = (
            KeyframePromptBuilder.FORBIDDEN_ELEMENTS if has_characters 
            else KeyframePromptBuilder.NO_PEOPLE_FORBIDDEN_ELEMENTS
        )
        
        # 组合完整提示词
        full_prompt = f"""
{KeyframePromptBuilder.CORE_STYLE}

SCENE CONTEXT:
{scene_context}

{previous_shot_context}

SHOT DESCRIPTION:
{shot_description}
{dialogue_hint}

{KeyframePromptBuilder.TECHNICAL_SPECS}

{forbidden_elements}

Remember: This is a REAL PHOTOGRAPH from a LIVE-ACTION FILM, not a digital creation.
"""
        return full_prompt.strip()
    
    @staticmethod
    def _build_scene_context(scene: MovieScene) -> str:
        """构建场景上下文"""
        scene_info = scene.scene or "A scene"
        
        # 提取场景关键信息
        context = f"Location and Setting: {scene_info}"
        
        return context
    
    @staticmethod
    def _build_character_context(shot: MovieShot, characters: List[MovieCharacter]) -> str:
        """构建角色上下文"""
        if not shot.characters or not characters:
            return ""
        
        # 获取出现在此镜头中的角色
        shot_char_names = shot.characters if isinstance(shot.characters, list) else []
        relevant_chars = [c for c in characters if c.name in shot_char_names]
        
        if not relevant_chars:
            return ""
        
        char_descriptions = []
        for char in relevant_chars:
            desc = f"- {char.name}"
            if char.visual_traits:
                desc += f": {char.visual_traits}"
            char_descriptions.append(desc)
        
        if char_descriptions:
            return f"CHARACTERS IN SHOT (Real actors):\n" + "\n".join(char_descriptions)
        
        return ""
    
    @staticmethod
    def _build_previous_shot_context(previous_shot: Optional[MovieShot]) -> str:
        """构建上一帧分镜上下文（用于视觉连续性）"""
        if not previous_shot:
            return """VISUAL CONTINUITY:
This is the FIRST shot in this scene. Use the scene image as the primary visual reference for environment, lighting, and atmosphere. Establish the visual foundation for subsequent shots."""
        
        # 有上一帧，提供连续性指导
        prev_description = previous_shot.shot or "Previous shot"
        
        context = f"""VISUAL CONTINUITY (Critical for seamless flow):
This shot CONTINUES from the previous shot. Maintain visual consistency:
- Previous shot description: {prev_description[:200]}
- Keep consistent lighting, color palette, and atmosphere
- Ensure smooth visual transition from previous frame
- Characters should maintain consistent appearance and positioning
- Environment elements should show logical progression"""
        
        return context


__all__ = ["KeyframePromptBuilder"]
