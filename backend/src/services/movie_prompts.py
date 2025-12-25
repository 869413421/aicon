"""
Movie Prompt Templates
电影工作流的所有Prompt模板集中管理
"""

class MoviePromptTemplates:
    """电影工作流Prompt模板管理器"""
    
    # 场景提取Prompt
    SCENE_EXTRACTION = """你是一名国际获奖级的电影编剧与导演，擅长将长篇小说章节转化为可直接用于电影制作与视频生成的结构化电影场景数据。

你的任务是：
**将以下小说章节拆分为多个电影场景（Scene），并为每一个场景生成高度具体、信息密度极高的电影级场景描述，同时标注该场景中出现的角色名称。**

---

## 【强约束规则（必须严格遵守）】

1. 你【不能】创造任何新角色  
2. 你【只能】使用我提供的「已存在角色列表」中的角色名字,角色名字必须完全一致，如 `梅露希亚 (Melusia)` 必须返回`梅露希亚 (Melusia)` ,不允许返回 `梅露希亚`
3. 场景中的 `characters` 只表示"出现的角色名字"，不区分主次  
4. 若某个场景没有任何角色出现，`characters` 必须为 `[]`  
5. 禁止在 JSON 中输出任何解释、注释、Markdown、代码块标记或多余文字  

---

## 已存在角色列表（只能从这里选择）：
{characters}

---

## 【输出格式（必须严格遵守）】

你必须 **只输出 JSON**，结构如下：

{{
  "scenes": [
    {{
      "order_index": 1,
      "scene": "高密度电影场景描述（见下方写作规范）",
      "characters": ["角色名1", "角色名2"]
    }}
  ]
}}

---

## 【Scene 字段写作规范（极其重要）】

`scene` 字段不是摘要，而是一段 **可直接被"看见"的电影文本**，必须尽可能详细、具体、连续，信息密度要高。

每一个 Scene 的描述应尽量包含以下内容（不需要显式分点）：

- **环境与空间**：地点、地形、建筑、天气、光线、时间感
- **声音要素**：环境音、脚步声、金属声、风声、雨声等
- **角色行动**：具体的肢体动作、位置变化、互动过程
- **冲突与张力**：对峙、追逐、威胁、犹豫、失控、爆发
- **对话内容**：重要对话直接写入，用引号标出，可适度精炼但必须保留原意
- **情绪呈现方式**：通过动作、语气、停顿、行为体现，禁止心理独白

Scene 描述应接近"剧本 + 文学描写"的融合，但始终以 **镜头可见内容** 为核心。

---

## 【场景拆分原则】

1. 一个 Scene 必须对应一个明确的时间与空间  
2. 当地点或时间发生明显变化时，必须拆分为新的 Scene  
3. 动作密集或冲突激烈的段落可以写得更长、更细  
4. 不写分镜、不写镜头语言、不写摄影术语  
5. 保持电影叙事节奏，避免整章只有一个 Scene  

---

## 【示例（仅用于理解信息密度与风格，不要照抄内容）】

{{
  "scenes": [
    {{
      "order_index": 1,
      "scene": "暴雨在夜色中倾泻而下，城墙外的碎石路被雨水冲刷成一条条反光的沟壑。城门半掩，腐朽的木门在狂风中不断撞击石框，发出沉闷的回响。阿尔德里克站在城门内侧，盔甲破损严重，左肩的铁甲已经裂开，鲜血顺着雨水缓慢流淌。他一手扶着城墙稳住身体，另一手紧握长剑，剑尖垂地，随着呼吸轻微颤抖。远处传来规律而沉重的脚步声，火把的光在雨幕中逐渐逼近。梅露希亚从队伍前方走出，停在城门外数步之遥，抬头说道："我以为你已经死在北境了。"阿尔德里克沉默片刻，将长剑重新提起，低声回应："我本来也希望如此。"风雨在两人之间翻涌，对峙的张力在城门内外不断积累。",
      "characters": ["阿尔德里克", "梅露希亚"]
    }},
    {{
      "order_index": 2,
      "scene": "黎明前的荒野一片死寂，薄雾贴着地面缓慢流动。焦黑的战旗倒插在泥土中，断裂的兵器散落四周，金属表面还残留着未干的血迹。风吹过草丛，发出低沉而空洞的声响，远处的乌鸦偶尔发出嘶哑的鸣叫。画面中没有任何角色出现，只剩下一场大战结束后的荒凉与空虚。",
      "characters": []
    }}
  ]
}}

---

## 【待改编小说章节】：
{text}
"""

    @classmethod
    def get_scene_extraction_prompt(cls, characters: str, text: str) -> str:
        """
        获取场景提取Prompt
        
        Args:
            characters: JSON格式的角色列表
            text: 小说章节内容
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.SCENE_EXTRACTION.format(characters=characters, text=text)

    # 分镜提取Prompt
    SHOT_EXTRACTION = """你是一名国际获奖级的电影编剧与导演，擅长将电影场景拆分为可直接用于拍摄的分镜头（Storyboard/Shot）。

你的任务是：
**将以下电影场景拆分为多个分镜（Shot），并为每一个分镜生成高度具体、信息密度极高的视觉描述，同时标注该分镜中出现的角色名称。**

---

## 【强约束规则（必须严格遵守）】

1. 你【不能】创造任何新角色
2. 你【只能】使用我提供的「已存在角色列表」中的角色名字，角色名字必须完全一致，如 `梅露希亚 (Melusia)` 必须返回 `梅露希亚 (Melusia)`，不允许返回 `梅露希亚`
3. 分镜中的 `characters` 只表示"出现的角色名字"，不区分主次
4. 若某个分镜没有任何角色出现，`characters` 必须为 `[]`
5. 禁止在 JSON 中输出任何解释、注释、Markdown、代码块标记或多余文字

---

## 已存在角色列表（只能从这里选择）：
{characters}

---

## 【输出格式（必须严格遵守）】

你必须 **只输出 JSON**，结构如下：

{{
  "shots": [
    {{
      "order_index": 1,
      "shot": "详细的分镜描述，包含人物动作、构图、光影、环境细节、对话等。",
      "dialogue": "角色对话内容（如果没有对话则为空字符串）",
      "characters": ["角色名1", "角色名2"]
    }}
  ]
}}

---

## 【Shot 字段写作规范（极其重要）】

`shot` 字段不是摘要，而是一段 **可直接被"看见"的画面文本**，必须尽可能详细、具体、连续，信息密度要高。

每一个 Shot 的描述应尽量包含以下内容（不需要显式分点）：

- **人物位置与动作**：具体的肢体动作、表情、眼神、姿态变化
- **构图与景别**：特写、中景、全景、俯视、仰视等
- **光影与色调**：光线方向、明暗对比、色彩氛围
- **环境细节**：背景元素、道具、空间关系
- **情绪呈现**：通过动作、表情、停顿体现，禁止心理独白
- **对话内容**：重要对话直接写入，用引号标出

Shot 描述应接近"分镜脚本 + 文学描写"的融合，但始终以 **镜头可见内容** 为核心。

---

## 【分镜拆分原则】

1. 一个 Shot 对应一个明确的镜头角度和时间段
2. 当镜头角度、景别、或人物动作发生明显变化时,应拆分为新的 Shot
3. 对话密集的段落可以按对话轮次拆分
4. 动作密集或冲突激烈的段落应拆分得更细，以便捕捉关键动作
5. 保持电影叙事节奏，避免整个场景只有一个 Shot
6. 每个 Shot 应该是一个可以独立成像的画面
7. 保证分镜连贯性，镜头切换要自然流畅

## 【分镜连贯性示例】

✅ 正确示例（流畅衔接）：
Shot 1: 全景 - 夜晚的城堡大厅，壁炉火光摇曳，长桌上摆满食物
Shot 2: 中景 - 阿尔德里克推门而入，雪花从外面飘进大厅
Shot 3: 特写 - 阿尔德里克疲惫的脸庞，眼神扫视大厅

❌ 错误示例（突兀跳转）：
Shot 1: 特写 - 阿尔德里克的眼睛
Shot 2: 全景 - 城外的森林
Shot 3: 特写 - 梅露希亚的手

## 【对话场景示例】

场景：两人对峙
Shot 1: 中景 - 阿尔德里克站在门口，握紧剑柄
Shot 2: 中景 - 梅露希亚转身面对他，手按在腰间匕首上
Shot 3: 特写 - 阿尔德里克开口："我以为你已经离开了。"
Shot 4: 特写 - 梅露希亚冷笑："你希望我离开？"

---

## 【待拆分场景】：
{scene}
"""

    @classmethod
    def get_shot_extraction_prompt(cls, characters: str, scene: str) -> str:
        """
        获取分镜提取Prompt
        
        Args:
            characters: JSON格式的角色列表
            scene: 场景描述
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.SHOT_EXTRACTION.format(characters=characters, scene=scene)

    # 场景图生成Prompt
    SCENE_IMAGE_GENERATION = """Create a cinematic environment shot for the following scene. 
Focus ONLY on the location, setting, and atmosphere. 
DO NOT include any people, characters, or human figures.

Scene Description:
{scene_description}

Requirements:
- High-quality cinematic photography
- Professional lighting and composition
- Detailed environment and atmosphere
- NO people, NO characters, NO humans
- Wide or establishing shot perspective
- Film-grade visual quality

Negative Prompt: people, characters, humans, person, man, woman, child, face, body"""

    @classmethod
    def get_scene_image_prompt(cls, scene_description: str) -> str:
        """
        获取场景图生成Prompt
        
        Args:
            scene_description: 场景描述
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.SCENE_IMAGE_GENERATION.format(scene_description=scene_description)

    # 过渡视频提示词生成Prompt
    TRANSITION_VIDEO = """你是一个国际获奖级的电影视频提示词生成专家。
请根据以下两个分镜的描述，生成一个用于AI视频生成的英文提示词。
这个提示词将用于生成两个分镜之间的过渡视频。

要求：
1. 提示词必须是英文
2. 描述要具体、详细，包含动作、光影、环境等细节
3. 确保两个分镜之间的过渡自然流畅
4. 只输出提示词本身，不要包含任何解释或标记
5. 提示词开头明确视频中对话使用中文
6. 场景中的声音和对话要使用自然语言描述
7. **角色名称必须与输入完全一致，不允许翻译、音译或修改（例如：输入是"李明"，输出也必须是"李明"，不能变成"Li Ming"或其他形式）**

两个分镜的描述：
{combined_text}

示例参考：

**重要提示：所有示例中的角色名称都保持原始中文形式，不进行任何翻译或音译！**

示例1（室内对话场景）：
输入：
分镜1: 特写，李明坐在办公桌前，表情严肃
对话: "这个项目必须在周五前完成"
角色: 李明
分镜2: 中景，王芳站起身，面露难色
对话: "时间太紧了，我需要更多人手"
角色: 王芳

输出：
Cinematic transition video with Chinese dialogue. Close-up of 李明 sitting at office desk with serious expression, saying "这个项目必须在周五前完成" in Chinese. Camera slowly pulls back revealing the modern office environment with soft overhead lighting. 王芳 gradually comes into frame, standing up from her chair with a worried expression, responding "时间太紧了，我需要更多人手" in Chinese. Natural office ambience with subtle keyboard typing sounds. Smooth camera movement creating seamless flow between the two shots.

示例2（动作场景）：
输入：
分镜1: 全景，张伟在街道上奔跑
对话: 无
角色: 张伟
分镜2: 特写，张伟停下脚步，气喘吁吁
对话: "终于甩掉他们了"
角色: 张伟

输出：
Dynamic action sequence with Chinese dialogue. Wide shot of 张伟 running through urban street, footsteps echoing on pavement. Camera follows his movement with smooth tracking shot. Gradual transition to close-up as he slows down and stops, breathing heavily. He catches his breath and says "终于甩掉他们了" in Chinese with relief. Urban street sounds, heavy breathing, distant traffic noise. Natural lighting with slight motion blur during running sequence.

示例3（情感场景）：
输入：
分镜1: 中景，小雨坐在窗边，望向窗外
对话: 无
角色: 小雨
分镜2: 特写，小雨的眼中泛起泪光
对话: "我真的很想念你"
角色: 小雨

输出：
Emotional cinematic moment with Chinese dialogue. Medium shot of 小雨 sitting by the window, gazing outside with melancholic expression. Soft natural window light illuminating her face. Camera slowly pushes in for intimate close-up, revealing tears welling up in her eyes. She whispers "我真的很想念你" in Chinese with emotional trembling voice. Quiet ambient sound with distant rain drops, creating contemplative atmosphere. Gentle camera movement emphasizing emotional depth.

现在请为上述两个分镜生成过渡视频提示词："""

    @classmethod
    def get_transition_video_prompt(cls, combined_text: str) -> str:
        """
        获取过渡视频提示词生成Prompt
        
        Args:
            combined_text: 组合的两个分镜描述
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.TRANSITION_VIDEO.format(combined_text=combined_text)


__all__ = ["MoviePromptTemplates"]
