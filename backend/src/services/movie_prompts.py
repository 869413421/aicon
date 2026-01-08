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

    # 分镜提取Prompt（九宫格方案 - 固定9个分镜）
    SHOT_EXTRACTION = """你是一名国际获奖级的电影分镜设计师与故事板艺术家，擅长创作连续流畅的电影分镜板（Storyboard）。

你的任务是：
**将以下电影场景转化为一个包含9个连续分镜的故事板，以3x3九宫格形式呈现，用于生成4K高清分镜板图像。**

---

## 【核心设计原则】

### 1. 九宫格布局规范
```
[格子1] [格子2] [格子3]
[格子4] [格子5] [格子6]
[格子7] [格子8] [格子9]

阅读顺序：从左到右，从上到下
时间流动：格子1（开始）→ 格子9（结束）
```

### 2. 固定9个分镜原则
- **必须恰好9个分镜**，不能多也不能少
- 每个分镜代表场景中的一个关键时刻
- 分镜之间必须有清晰的**视觉连续性**和**叙事递进**

### 3. 8秒视频适配
- 每个分镜最终将生成8秒视频
- 分镜描述必须包含**起始状态**和**结束状态**
- 动作必须在8秒内可完成，避免过于复杂的动作序列

---

## 【强约束规则（必须严格遵守）】

1. 你【不能】创造任何新角色  
2. 你【只能】使用我提供的「已存在角色列表」中的角色名字
3. 角色名字必须完全一致，如 `梅露希亚 (Melusia)` 必须返回 `梅露希亚 (Melusia)`
4. `characters` 字段只表示该分镜中出现的角色名字列表，不区分主次
5. 若某个分镜中没有任何角色出现，`characters` 必须为 `[]`
6. **只输出 JSON**，禁止输出任何解释、注释、Markdown、代码块或多余文本

---

## 已存在角色列表（只能从这里选择）：
{characters}

---

## 【输出格式（必须严格遵守）】

{{
  "shots": [
    {{
      "order_index": 1,
      "shot": "完整的分镜描述（包含运镜、光线、画面、动作等所有信息，见下方规范）",
      "dialogue": "角色对话内容（若无对话则为空字符串）",
      "characters": ["角色名1"]
    }},
    {{
      "order_index": 2,
      "shot": "...",
      "dialogue": "...",
      "characters": ["角色名1", "角色名2"]
    }}
    // ... 共9个分镜
  ]
}}

---

## 【创意运镜技巧库】

### 经典电影运镜手法

#### 1. **希区柯克变焦 (Dolly Zoom / Vertigo Effect)**
- **效果**: 背景拉伸或压缩，主体大小不变，营造眩晕、不安、顿悟感
- **适用场景**: 角色震惊、恐惧、顿悟时刻

#### 2. **一镜到底 (Long Take / Oner)**
- **效果**: 流畅连续的视觉体验，沉浸感强
- **适用场景**: 追逐、对话、环境展示

#### 3. **荷兰角 (Dutch Angle / Canted Angle)**
- **效果**: 画面倾斜，营造不安、混乱、紧张感
- **适用场景**: 心理失衡、危机时刻、反派视角

#### 4. **鸟瞰镜头 (Bird's Eye View / Top-Down Shot)**
- **效果**: 上帝视角，展现空间关系和角色渺小感
- **适用场景**: 战场全景、角色孤立、命运感

#### 5. **低角度仰拍 (Low Angle Shot)**
- **效果**: 角色显得高大、威严、有力量
- **适用场景**: 展现权威、威胁、英雄时刻

### 现代创意运镜

#### 6. **穿越机镜头 (FPV Drone Shot)**
- **效果**: 极速穿梭、灵活机动、第一人称视角
- **适用场景**: 追逐、探索、动作高潮

#### 7. **环绕镜头 (Orbital Shot / 360° Rotation)**
- **效果**: 全方位展示主体，时间静止感
- **适用场景**: 角色亮相、关键物品展示、战斗场面

#### 8. **子弹时间 (Bullet Time)**
- **效果**: 极慢动作配合环绕，时空凝固感
- **适用场景**: 关键动作瞬间、子弹飞行、武打

#### 9. **推轨变焦 (Push In + Rack Focus)**
- **效果**: 焦点转移，引导观众注意力
- **适用场景**: 揭示隐藏信息、情绪转折

#### 10. **手持跟拍 (Handheld Follow)**
- **效果**: 纪实感、紧张感、真实感
- **适用场景**: 逃跑、战斗、混乱场面

### 运镜选择指南

**对话场景**: 推轨特写 (Slow push in)、过肩镜头 (Over-the-shoulder)、推轨变焦 (Push in + rack focus)

**动作场景**: 穿越机 (FPV drone)、手持跟拍 (Handheld follow)、环绕镜头 (Orbital shot)、子弹时间 (Bullet time)

**情绪高潮**: 希区柯克变焦 (Dolly zoom)、荷兰角 (Dutch angle)、螺旋上升 (Spiral ascent)

**环境展示**: 鸟瞰镜头 (Bird's eye view)、一镜到底 (Long take)、反向运动 (Reverse dolly)

**紧张/恐怖**: 低角度仰拍 (Low angle)、荷兰角 (Dutch angle)、第一人称POV (First-person POV)

---

## 【Shot描述写作规范（极其重要）】

每个 `shot` 字段必须是 **完整的电影分镜描述**，包含所有必要信息：

### 必需元素（按顺序整合到shot字段中）：

1. **运镜方式**（放在开头）：
   - 明确说明使用的运镜手法（参考创意运镜技巧库）
   - 例如："希区柯克变焦"、"穿越机镜头"、"推轨特写"
   - 格式：`[运镜名称]: [运镜描述]`

2. **光线与氛围**：
   - 光线条件：golden hour sunlight, dramatic shadows, soft diffused light
   - 色调：warm tones, cool tones, high contrast
   - 天气：clear sky, rainy, foggy

3. **起始画面状态**：
   - 角色位置、姿态、表情
   - 环境元素、道具位置
   - 构图和景别（特写/中景/全景）

4. **连续可见动作**（8秒内完成）：
   - 具体的肢体动作、位置变化
   - 物体移动、环境变化
   - 表情和情绪的视觉呈现

5. **结束画面状态**：
   - 动作完成后的最终姿态
   - 画面稳定状态
   - 为下一格做好视觉铺垫（视觉衔接点）

### 整合格式示例：

✅ **完整的shot描述示例**：

"Slow push in: 黄昏暖光透过破碎的城门洒入，营造出金色的光影对比。中景镜头。阿尔德里克站在城门内侧，盔甲破损严重，左肩铁甲裂开，鲜血顺着雨水缓慢流淌。他一手扶着城墙稳住身体，另一手紧握长剑，剑尖垂地，随着呼吸轻微颤抖。镜头缓慢推进，聚焦他疲惫但坚定的眼神。雨水打在脸上，他深吸一口气，将长剑重新提起，剑尖从垂地状态抬升至胸前防御姿态。最终画面定格在他警戒的姿态，视线望向城门外，为下一格的对峙做好铺垫。"

"FPV drone shot: 穿越机镜头从城门外高速穿入，以第一人称视角展现梅露希亚的队伍逼近。夜色中火把的光在雨幕中摇曳，营造紧张氛围。镜头快速穿过半掩的城门，在狭窄空间中灵活机动，最终定格在梅露希亚从队伍前方走出的画面。她停在城门外数步之遥，抬头望向阿尔德里克，雨水顺着她的盔甲流淌。镜头稳定在她坚定的表情上，为对话做好准备。"

### 禁止元素：
- ❌ 心理描写或内心独白
- ❌ 抽象情绪总结（如"他感到悲伤"）
- ❌ 无法在8秒内完成的复杂动作
- ❌ 过于模糊的描述（如"一些东西"）
- ❌ 将运镜、光线、画面分开描述（必须整合）

---

## 【九宫格视觉连续性设计】

### 关键原则：
1. **统一视觉风格**：
   - 所有9个格子使用相同的光线条件（如：黄昏暖光）
   - 保持一致的色调和对比度
   - 角色外观（服装、发型、妆容）完全一致

2. **流畅的叙事节奏**：
   ```
   格子1-3：场景建立 + 冲突引入
   格子4-6：冲突发展 + 高潮铺垫
   格子7-9：高潮爆发 + 情绪落点
   ```

3. **视觉衔接技巧**：
   - **动作延续**：上一格的结束动作在下一格继续
   - **视线引导**：角色视线方向引导到下一格的焦点
   - **空间连贯**：保持环境元素的位置关系
   - **光影过渡**：光线变化自然渐进

4. **对话分配**：
   - 每个格子最多1-2句关键对话
   - 对话必须伴随明确的可见动作
   - 避免连续多格都是对话（会导致视觉单调）

---

## 【分镜拆分策略】

### 简单对话场景（2-3人对话）：
```
格子1: 建立镜头（环境 + 角色位置）
格子2-3: 角色A说话（不同角度）
格子4-5: 角色B回应（表情变化）
格子6-7: 互动细节（手势、眼神）
格子8: 情绪转折点
格子9: 结束画面（为下一场景铺垫）
```

### 动作场景（追逐、打斗）：
```
格子1: 动作起始（蓄力、准备）
格子2-4: 动作展开（连续动作分解）
格子5-6: 冲突高潮（碰撞、对抗）
格子7-8: 结果呈现（倒地、逃离）
格子9: 余波（环境破坏、角色状态）
```

### 环境展示场景（无角色或角色为背景）：
```
格子1: 远景建立（整体环境）
格子2-4: 环境细节扫描（建筑、地形）
格子5-6: 氛围元素（天气、光线变化）
格子7-8: 角色进入（如有）
格子9: 场景稳定（为后续动作准备）
```

---

## 【待拆分场景】

{scene}

---

## 【生成检查清单】

在输出前，请确认：
- [ ] 是否恰好9个分镜？
- [ ] 每个shot字段是否包含运镜方式（放在开头）？
- [ ] 每个shot字段是否包含光线与氛围描述？
- [ ] 每个分镜是否包含起始和结束状态？
- [ ] 每个分镜是否包含视觉衔接点（为下一格铺垫）？
- [ ] 角色名称是否完全一致？
- [ ] 视觉风格是否统一（光线、色调）？
- [ ] 对话是否自然融入画面动作？
- [ ] 是否避免了心理描写和抽象情绪？
- [ ] 每个动作是否能在8秒内完成？
- [ ] 是否将所有信息整合到shot字段中（不分散）？

**请严格按照上述要求，生成一个完整的九宫格分镜板JSON。只输出JSON本身，不要有任何额外说明。**
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
    SCENE_IMAGE_GENERATION = """Create a cinematic establishing shot of the following environment.
This is a LIVE-ACTION PHOTOGRAPH for a film production, not CGI or 3D render.

## Scene Description
{scene_description}

## Prompt Structure (Apply Veo 3.1 Formula)

### [Cinematography]
Choose appropriate camera work for establishing the environment:
- Camera angle: Wide establishing shot, aerial view, crane shot, sweeping panorama, high angle (show scope), eye-level perspective
- Composition: Rule of thirds, leading lines, depth layers (foreground/midground/background), balanced framing
- Lens: Wide-angle lens for expansive views, deep focus to capture environmental detail

### [Environment Subject]
The location and setting itself is the subject:
- Identify the main environmental elements (landscape, architecture, interior space, natural features)
- Emphasize spatial relationships and scale
- Highlight distinctive characteristics of the location

### [Atmospheric Context]
Define the temporal and weather conditions:
- Time of day: Golden hour (warm sunset/sunrise light), blue hour (twilight), midday sun, overcast day, night
- Weather: Clear skies, scattered clouds, fog/mist, light rain, snow, storm clouds gathering
- Season: Spring bloom, summer lushness, autumn colors, winter bareness (if relevant)

### [Style & Ambiance]
Establish the mood and visual aesthetic:
- Lighting quality: Soft diffused natural light, dramatic shadows and highlights, volumetric light rays through atmosphere, ambient environmental glow, harsh direct sunlight
- Mood: Serene and peaceful, ominous and foreboding, mysterious and enigmatic, vibrant and lively, desolate and abandoned, welcoming and warm
- Aesthetic: Cinematic film photography, photorealistic, rich color palette or muted tones, high dynamic range

## Critical Requirements

**UNINHABITED ENVIRONMENT - No Human Presence:**
- This is a pristine, empty, deserted location
- Vacant space with no people, figures, or human activity
- Unpopulated natural landscape or abandoned built environment
- No human silhouettes, shadows, or reflections
- No crowds, groups, individuals, or any human-like shapes
- The environment exists in complete solitude

**Technical Specifications:**
- Shot on professional cinema camera (ARRI Alexa, RED, Sony Venice)
- Cinematic color grading with film look (not digital/video look)
- High dynamic range with rich environmental detail
- Professional landscape or architectural photography standards
- Natural depth of field characteristic of cinema lenses

**Forbidden Elements:**
- NO 3D rendering artifacts or CGI aesthetics
- NO video game or synthetic imagery look
- NO people, characters, humans, persons, faces, bodies
- NO human-made activity or human presence indicators
- NO mannequins or human-shaped objects

Generate a detailed, cinematic establishing shot that captures the essence and atmosphere of this environment."""

    @classmethod
    def get_scene_image_prompt(cls, scene_description: str) -> str:
        """
        获取场景图生成Prompt (基于原始场景描述)
        
        Args:
            scene_description: 场景描述
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.SCENE_IMAGE_GENERATION.format(scene_description=scene_description)
    
    # 基于分镜描述的场景图生成Prompt
    SCENE_IMAGE_FROM_SHOTS = """Create a cinematic establishing shot based on the visual elements described in the following shots.
This is a LIVE-ACTION PHOTOGRAPH for a film production, not CGI or 3D render.

## Shots Description
{shots_description}

## Your Task
Analyze the shots above and extract the COMMON ENVIRONMENTAL ELEMENTS that appear across these shots.
Focus on creating an establishing shot that shows the LOCATION and ATMOSPHERE where these shots take place.

### Extract These Elements:
1. **Location Type**: Indoor/outdoor, specific place (office, street, castle, etc.)
2. **Architectural Details**: Buildings, structures, room layout, furniture placement
3. **Lighting Conditions**: Time of day, light sources, shadows, atmosphere
4. **Weather/Atmosphere**: Clear, rainy, foggy, stormy, etc.
5. **Color Palette**: Dominant colors, tones, mood
6. **Spatial Layout**: How the space is organized, key landmarks

### Generate Establishing Shot Prompt:

Use Veo 3.1 Formula:
- **[Cinematography]**: Wide establishing shot, appropriate angle to show the space
- **[Environment Subject]**: The location itself (NO people, NO characters)
- **[Atmospheric Context]**: Time of day, weather, lighting from the shots
- **[Style & Ambiance]**: Mood and aesthetic matching the shots

## Critical Requirements

**UNINHABITED ENVIRONMENT - No Human Presence:**
- Extract ONLY the environment from the shots, remove ALL human elements
- This is a pristine, empty, deserted location
- NO people, characters, humans, persons, faces, bodies
- NO human silhouettes, shadows, or reflections
- The environment exists in complete solitude

**Match the Shots' Visual Style:**
- Use the same lighting conditions described in the shots
- Match the time of day and weather
- Maintain the same color palette and mood
- Ensure the establishing shot feels like it belongs to the same scene

**Technical Specifications:**
- Shot on professional cinema camera (ARRI Alexa, RED, Sony Venice)
- Cinematic color grading with film look
- High dynamic range with rich environmental detail
- Professional landscape or architectural photography standards

**FORBIDDEN - ABSOLUTELY NO:**
- ❌ 3D rendering or CGI aesthetics
- ❌ Computer-generated imagery of any kind
- ❌ Video game graphics or synthetic visuals
- ❌ Perfect geometric shapes or artificial smoothness
- ❌ Unnatural lighting or impossible light sources
- ❌ Overly saturated or artificial colors
- ❌ Clean, perfect surfaces (real world has imperfections)

Generate a detailed, cinematic establishing shot that captures the environment where these shots take place."""

    @classmethod
    def get_scene_image_prompt_from_shots(cls, shots_description: str) -> str:
        """
        基于分镜描述生成场景图提示词
        
        Args:
            shots_description: 场景的所有分镜描述(组合)
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.SCENE_IMAGE_FROM_SHOTS.format(shots_description=shots_description)

    # 过渡视频提示词生成Prompt
    TRANSITION_VIDEO = """你是一名精通 **Google Veo 3.1** 的电影级视频提示词生成专家。

你的任务是：
**仅生成"当前分镜"的 8 秒视频内容。**

⚠️ **重要上下文说明（不属于生成内容）：**

* 前一个分镜已完整呈现，不得在本视频中重复、回放、延续或重新表现
* 本视频 **必须从当前分镜的起始状态直接开始**
* 前一个分镜的信息仅用于理解上下文连续性，绝对不能被生成到视频中

---

### 【前一个分镜（仅作上下文参考，禁止生成）】

{previous_shot}

---

### 【当前分镜（这是你要生成的内容）】

{current_shot}

---

### 【核心硬性约束】

* 时长固定：**8 秒**
* **单一连续镜头**（no cuts, no transitions）
* 不得出现前一分镜中的具体动作、物体或细节
* 不得回看、回溯、延迟进入状态
* 不得引入新角色、新道具、新场景
* 所有变化在尾帧画面中必须成立

---

### 【输出结构（严格遵守）】

只输出以下五个部分，不要任何解释文字。

---

### [Cinematography] 摄影与镜头

描述镜头类型、运动方式、景别、焦距、构图。
* 镜头运动：dolly shot, tracking shot, slow pan, push in, pull back, arc shot, handheld, steadicam
* 景别：wide shot, medium shot, close-up, extreme close-up, over-the-shoulder
* 焦距：shallow depth of field, deep focus, rack focus
* 构图：rule of thirds, centered framing, leading lines, symmetrical composition
* **单一连续镜头，无剪辑、无转场**

---

### [Subject] 主体状态

列出所有角色（名称必须与输入完全一致），描述：
* 起始状态：简要概括（不超过1句话）
* 结束状态：简要概括（不超过1句话）

**注意：不要复述前一分镜的细节，只描述当前分镜的状态变化**

---

### [Action] 8 秒连续动作（唯一时间轴）

* **0–2 秒**：起始动作或静态建立（用自己的语言简述首帧状态）
* **2–6 秒**：核心动作展开（重点描述过渡过程中的动作变化）
* **6–8 秒**：动作完成与画面稳定（用自己的语言简述尾帧状态）

**如果当前分镜中有对话，必须在适当时间点自然融入。**

**对话语言判断规则：**
* 中文名角色（如：李明、梅露希亚）→ 对话使用中文
* 英文名角色（如：Marcus Thorne、Leo）→ 对话使用英文
* 根据场景语境判断，无法判断时默认使用中文

**对话格式：**
* 使用引号包裹对话内容
* 在对话前简要说明说话者和语气
* 例如：`马库斯·索恩 (Marcus Thorne) 用低沉嘶哑的声音说："Don't look at it, kid."`

---

### [Context] 环境与声音

描述场景位置、光线、时间、天气、环境音效。

**音频规则（极其重要）：**
* ❌ 严格禁止任何背景音乐（NO background music, NO BGM, NO soundtrack, NO score）
* ✅ 只允许真实环境声音：
  - **物理音效**（使用前缀）：`SFX: footsteps on wooden floor, fabric rustling, heavy breathing, door creaking, glass breaking, metal clanging`
  - **环境音**（使用前缀）：`Ambient noise: room tone, wind through trees, distant traffic, rain on windows, crowd murmur`
  - **对话音**（如有）：`Dialogue: clear speech, natural voice`

---

### [Style & Ambiance] 风格与氛围

描述视觉风格、色调、情绪氛围。
* 视觉风格：live-action realism, cinematic, photorealistic, filmic
* 色调：warm tones, cool tones, high contrast, muted colors, vibrant palette
* 情绪氛围（通过可见画面状态体现，禁止抽象描述）

---

**必须在末尾声明：**
NO background music, NO BGM, NO soundtrack, only natural sound effects and ambient noise.

---

### 【生成检查清单】

- [ ] 是否只生成了当前分镜的内容？
- [ ] 是否避免了重复前一分镜的具体细节？
- [ ] 如果有对话，是否已包含在 [Action] 部分？
- [ ] 对话语言是否根据角色名称正确判断？
- [ ] 是否声明了禁止背景音乐？

**请严格按照上述要求，生成一个完整的8秒视频中文提示词。只输出提示词本身，不要有任何额外说明。**
"""


    @classmethod
    def get_transition_video_prompt(cls, previous_shot: str, current_shot: str) -> str:
        """
        获取过渡视频提示词生成Prompt
        
        Args:
            previous_shot: 前一个分镜描述（仅作上下文参考）
            current_shot: 当前分镜描述（要生成的内容）
            
        Returns:
            str: 格式化后的prompt
        """
        return cls.TRANSITION_VIDEO.format(previous_shot=previous_shot, current_shot=current_shot)


__all__ = ["MoviePromptTemplates"]
