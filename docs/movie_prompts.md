# 电影生成Prompt模板完整文档

本文档包含AICON2电影生成流程中使用的所有Prompt模板的完整内容。

---

## 目录

1. [角色提取Prompt](#1-角色提取prompt)
2. [角色三视图生成Prompt](#2-角色三视图生成prompt)
3. [场景提取Prompt](#3-场景提取prompt)
4. [分镜提取Prompt](#4-分镜提取prompt)
5. [场景图生成Prompt](#5-场景图生成prompt)
6. [关键帧生成Prompt](#6-关键帧生成prompt)
7. [过渡视频Prompt生成](#7-过渡视频prompt生成)

---

## 1. 角色提取Prompt

**用途**: 从章节内容中提取所有主要角色及其特征

**文件位置**: `backend/src/services/movie_character_service.py`

**输入变量**:
- `{text}`: 章节内容(限制5000字符)

**输出格式**: JSON

### 完整Prompt

```
你是一个资深的选角导演。请分析以下电影剧本片段,提取出其中出现的所有主要角色。

### 输出要求:
必须以 JSON 格式输出,结构如下:
{
  "characters": [
    {
      "name": "角色姓名",
      "era_background": "时代背景(如: 1940s WWII, Victorian Era, Cyberpunk 2077, Modern era等)",
      "occupation": "职业或社会地位",
      "role_description": "角色的身份、背景、性格特点",
      "visual_traits": "详细的视觉特征描述(如:年龄、发色、发型、穿着、面部特征、体型),用于AI生图。",
      "key_visual_traits": ["核心视觉特征1", "核心视觉特征2", "核心视觉特征3"],
      "dialogue_traits": "角色的对话风格(如:冷静、粗鲁、幽默、书生气、口音特点等)"
    }
  ]
}

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
```

---

## 2. 角色三视图生成Prompt

**用途**: 生成角色的三视图定妆照(前视图、侧视图、背视图)

**文件位置**: `backend/src/services/movie_character_service.py` - `CharacterThreeViewPromptBuilder`

**输入变量**:
- `{name}`: 角色名称
- `{era_background}`: 时代背景
- `{occupation}`: 职业
- `{key_visual_traits}`: 核心视觉特征

**输出格式**: 英文图像生成提示词

### 完整Prompt模板

```
CINEMATIC LIVE-ACTION CHARACTER REFERENCE
featuring THREE CONSISTENT PHOTOGRAPHED VIEWS
of the SAME REAL HUMAN ACTOR portraying {name}:

front view, 90-degree side view, and back view,
captured during the same on-set studio photoshoot.

Character details:
- Name: {name}
- Era / Time Period: {era_background}
- Occupation / Social Status: {occupation}
- Key Visual Traits: {key_visual_traits}

Live-Action Photography Requirements:
- Portrayed by ONE real human actor
- All three views show the SAME actor, SAME costume, SAME makeup
- Natural human skin texture with pores, imperfections, micro-details
- Real fabric materials, real metal wear, practical costume design
- Identical hairstyle, body proportions, posture across all views
- Neutral production stance for film reference

Cinematography & Photography Style:
- High-end live-action film stills
- Shot on professional cinema camera (ARRI / RED style look)
- Real studio lighting, soft key light, natural shadows
- Photographed, not rendered
- Neutral or black studio background

STRICT CONSTRAINTS:
- NO 3D render
- NO CGI
- NO Unreal Engine
- NO game character style
- NO digital sculpt look

Technical Output:
- Ultra-detailed live-action character reference photos
- Aspect ratio: 16:9
- Place the English name in the top-left corner, clearly visible and readable
```

---

## 3. 场景提取Prompt

**用途**: 将章节内容拆分为多个电影场景

**文件位置**: `backend/src/services/movie_prompts.py` - `MoviePromptTemplates.SCENE_EXTRACTION`

**输入变量**:
- `{characters}`: JSON格式的角色名称列表
- `{text}`: 章节内容

**输出格式**: JSON

### 完整Prompt

```
你是一名国际获奖级的电影编剧与导演，擅长将长篇小说章节转化为可直接用于电影制作与视频生成的结构化电影场景数据。

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
```

---

## 4. 分镜提取Prompt

**用途**: 将场景拆分为多个分镜头

**文件位置**: `backend/src/services/movie_prompts.py` - `MoviePromptTemplates.SHOT_EXTRACTION`

**输入变量**:
- `{characters}`: JSON格式的角色名称列表
- `{scene}`: 场景描述

**输出格式**: JSON

### 完整Prompt

```
你是一名国际获奖级的电影编剧与导演，擅长将电影场景拆分为可直接用于拍摄的分镜头（Storyboard/Shot）。

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

## 【分镜拆分原则 - 适配8秒固定时长】

**核心哲学**: "每个8秒都要物有所值,减少总镜头数,提高内容密度"

### 重要提示
- 生成的每个分镜将用于生成**固定8秒**的视频
- 因此每个分镜描述应该设计为在8秒内完成的内容
- 优先在一个8秒镜头内包含更多叙事元素,而非拆分成多个镜头

### 1. 内容密度优先
每个8秒镜头应该包含:
- **多个动作**: 不要只描述单一简单动作(如"角色转身"),而应包含连续动作序列
- **多轮对话**: 一个8秒镜头可以包含2-3轮对话,不要每句话都拆分
- **环境+角色**: 同时描述环境和角色行为,充分利用8秒

### 2. 镜头数量控制
- **简单场景**: 2-3个镜头(16-24秒总时长)
- **对话场景**: 3-5个镜头(24-40秒总时长)
- **复杂动作场景**: 4-6个镜头(32-48秒总时长)
- **目标**: 每个场景平均3-5个镜头,而非10-15个

### 3. 只在以下情况拆分新镜头
- **视角重大切换**: 从全景切换到特写,从角色A切换到角色B的独立视角
- **空间转换**: 从一个房间到另一个房间,从室内到室外
- **时间跳跃**: 明确的时间流逝(如"片刻后"、"数小时后")
- **叙事节奏变化**: 从缓慢到快速,从平静到紧张的重大转折
- **关键情绪转折**: 需要特写强调的重要情绪变化

### 4. 避免拆分的情况
- ❌ 不要为单一简单动作创建镜头(如"角色转身"、"角色坐下")
- ❌ 不要为每句对话创建镜头
- ❌ 不要为小的角度变化创建镜头
- ❌ 不要为连续动作创建多个镜头(如跑步、跳跃、翻滚应该在一个镜头内)

### 5. 对话场景策略(关键!)
**8秒可以包含2-3轮对话**:
- 使用双人镜头(Two-Shot)包含完整对话
- 只在情绪高潮或关键台词时切换到特写
- 避免"切-反切"模式导致的过度碎片化

**示例**:
✅ 正确(1个8秒镜头):
"Medium two-shot. 李明 says in Chinese \"这个项目很重要\" while standing. 王芳 nods and responds in Chinese \"我明白,我会尽力\" with determined expression. 李明 smiles slightly."

❌ 错误(拆成3个镜头):
镜头1: 李明说话
镜头2: 王芳点头
镜头3: 王芳回应

### 6. 动作场景策略
**8秒可以包含一个完整动作序列**:
- 连续动作应该在一个镜头内完成
- 例如: 跑步+跳跃+翻滚+站起 = 1个8秒镜头
- 不要拆成4个单独的镜头

### 7. 保证分镜连贯性
- 镜头切换要自然流畅
- 每个镜头应该是一个可以独立成像的画面
- 避免突兀跳转

## 【推荐拆分示例 - 基于8秒固定时长】

### ✅ 优秀示例(内容密集,避免碎片化):

**场景: 办公室对峙(3镜头 = 24秒)**

Shot 1 (建立+开场, 8秒):
全景 - 现代办公室夜景,落地窗外城市灯光。李明坐在办公桌后审阅文件,表情严肃。王芳推门而入,脚步声在空旷办公室回荡,她走向办公桌。

Shot 2 (核心对话, 8秒):
双人中景 - 隔着办公桌对峙。王芳身体前倾,双手撑在桌面,直视李明说道:"这个项目必须在周五前完成。"李明缓缓站起,与她对视,回应:"时间太紧了,我需要重新评估。"两人对峙持续,张力积累。

Shot 3 (转折+结束, 8秒):
特写 - 李明的脸庞,他转身望向窗外,背对王芳。沉默片刻后说:"给我三天。"窗外光线照亮他的侧脸。

**分析**: 3个8秒镜头完成完整对话,Shot 2包含2轮对话,避免每句话都切换

---

### ❌ 错误示例(过度碎片化,避免):

Shot 1: 全景 - 办公室环境
Shot 2: 中景 - 王芳推门
Shot 3: 中景 - 王芳走路
Shot 4: 特写 - 李明抬头
Shot 5: 特写 - 王芳说话:"这个项目必须在周五前完成"
Shot 6: 特写 - 李明回应:"时间太紧了"
Shot 7: 特写 - 王芳继续说话
Shot 8: 中景 - 李明站起来
Shot 9: 特写 - 两人对视
Shot 10: 特写 - 李明转身

**问题**: 10个镜头,每个8秒只包含单一元素,过度碎片化,浪费了8秒的内容承载能力

---

## 【待拆分场景】：
{scene}
```

---

## 5. 场景图生成Prompt

**用途**: 生成场景的环境建立镜头(无人物)

**文件位置**: `backend/src/services/movie_prompts.py` - `MoviePromptTemplates.SCENE_IMAGE_GENERATION`

**输入变量**:
- `{scene_description}`: 场景描述

**输出格式**: 英文图像生成提示词

### 完整Prompt

```
Create a cinematic establishing shot of the following environment.
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

Generate a detailed, cinematic establishing shot that captures the essence and atmosphere of this environment.
```

---

## 6. 关键帧生成Prompt

**用途**: 为分镜生成关键帧图片,支持视觉连续性(接力式生成)

**文件位置**: `backend/src/services/keyframe_prompt_builder.py` - `KeyframePromptBuilder`

**输入变量**:
- `{shot}`: 分镜对象
- `{scene}`: 场景对象
- `{characters}`: 角色列表
- `{custom_prompt}`: 自定义提示词(可选)
- `{previous_shot}`: 上一个分镜对象(可选,用于视觉连续性)

**输出格式**: 英文图像生成提示词

### 核心特性

#### 视觉连续性支持
- **第一个分镜**: 使用场景图作为主要视觉参考,建立场景的视觉基础
- **后续分镜**: 引用上一个分镜的描述,保持光线、色调、氛围一致

#### 参考图策略
- **第一个分镜**: 场景图 + 角色头像
- **后续分镜**: 上一个分镜的关键帧 + 角色头像

### Prompt结构

```
CRITICAL STYLE REQUIREMENTS:
- This MUST be a LIVE-ACTION PHOTOGRAPH, not 3D render, not CGI, not animation
- Real human actors in real physical locations
- Captured with professional cinema cameras (ARRI, RED, Sony Venice)
...

SCENE CONTEXT:
{场景描述}

VISUAL CONTINUITY:
[第一个分镜]
This is the FIRST shot in this scene. Use the scene image as the primary visual reference 
for environment, lighting, and atmosphere. Establish the visual foundation for subsequent shots.

[后续分镜]
This shot CONTINUES from the previous shot. Maintain visual consistency:
- Previous shot description: {上一个分镜描述}
- Keep consistent lighting, color palette, and atmosphere
- Ensure smooth visual transition from previous frame
- Characters should maintain consistent appearance and positioning
- Environment elements should show logical progression

SHOT DESCRIPTION:
{分镜描述}
{对话内容(如果有)}

CHARACTERS IN SHOT (Real actors):
- {角色名}: {视觉特征}
...

Technical Specifications:
...

ABSOLUTELY FORBIDDEN:
- NO 3D rendering artifacts
- NO CGI character models
...
```

### 示例

#### 示例1: 第一个分镜(无人物)

**输入**:
- 场景: 暴雨中的城墙外,夜晚
- 分镜: 全景镜头,城墙在雨中矗立,城门半掩
- 角色: 无
- 上一个分镜: 无

**生成的Prompt**:
```
CRITICAL STYLE REQUIREMENTS:
- This MUST be a LIVE-ACTION PHOTOGRAPH, not 3D render, not CGI, not animation
- Real human actors in real physical locations
- Captured with professional cinema cameras (ARRI, RED, Sony Venice)
...

SCENE CONTEXT:
Location and Setting: 暴雨在夜色中倾泻而下,城墙外的碎石路被雨水冲刷成一条条反光的沟壑...

VISUAL CONTINUITY:
This is the FIRST shot in this scene. Use the scene image as the primary visual reference 
for environment, lighting, and atmosphere. Establish the visual foundation for subsequent shots.

SHOT DESCRIPTION:
全景镜头,城墙在雨中矗立,城门半掩,腐朽的木门在狂风中不断撞击石框,发出沉闷的回响。

Technical Specifications:
- Shot on 35mm film or high-end digital cinema camera
- Cinematic color grading (film look, not digital/game look)
...

ABSOLUTELY FORBIDDEN:
- NO 3D rendering artifacts
- NO people, human figures, characters, or persons of any kind
...
```

#### 示例2: 后续分镜(有人物)

**输入**:
- 场景: 暴雨中的城墙外,夜晚
- 分镜: 中景,阿尔德里克站在城门内侧,盔甲破损,手握长剑
- 角色: 阿尔德里克
- 上一个分镜: 全景镜头,城墙在雨中矗立

**生成的Prompt**:
```
CRITICAL STYLE REQUIREMENTS:
- This MUST be a LIVE-ACTION PHOTOGRAPH, not 3D render, not CGI, not animation
...

SCENE CONTEXT:
Location and Setting: 暴雨在夜色中倾泻而下,城墙外的碎石路被雨水冲刷成一条条反光的沟壑...

VISUAL CONTINUITY (Critical for seamless flow):
This shot CONTINUES from the previous shot. Maintain visual consistency:
- Previous shot description: 全景镜头,城墙在雨中矗立,城门半掩,腐朽的木门在狂风中不断撞击石框,发出沉闷的回响。
- Keep consistent lighting, color palette, and atmosphere
- Ensure smooth visual transition from previous frame
- Characters should maintain consistent appearance and positioning
- Environment elements should show logical progression

SHOT DESCRIPTION:
中景,阿尔德里克站在城门内侧,盔甲破损严重,左肩的铁甲已经裂开,鲜血顺着雨水缓慢流淌。
他一手扶着城墙稳住身体,另一手紧握长剑,剑尖垂地,随着呼吸轻微颤抖。

CHARACTERS IN SHOT (Real actors):
- 阿尔德里克: 中年战士,盔甲破损,沧桑面容,坚毅眼神

Technical Specifications:
...

ABSOLUTELY FORBIDDEN:
- NO 3D rendering artifacts
- NO CGI character models
...
```

### 关键点

1. **视觉连续性**: 通过在提示词中明确引用上一帧的描述,引导AI保持一致的视觉风格
2. **参考图优先级**: 上一帧关键帧 > 场景图,确保接力式的视觉传承
3. **错误处理**: 如果场景没有场景图且没有上一帧,抛出异常要求先生成场景图
4. **无人物场景**: 使用更严格的禁止列表,明确排除任何人物元素

---

## 7. 过渡视频Prompt生成

**用途**: 生成两个分镜之间的过渡视频提示词

**文件位置**: `backend/src/services/movie_prompts.py` - `MoviePromptTemplates.TRANSITION_VIDEO`

**输入变量**:
- `{combined_text}`: 组合的两个分镜描述(包含分镜描述、对话、角色)

**输出格式**: 英文视频生成提示词

### 完整Prompt

```
你是一个国际获奖级的电影视频提示词生成专家，精通 Veo 3.1 视频生成最佳实践。
请根据以下两个分镜的描述，生成一个用于 AI 视频生成的英文提示词。
这个提示词将用于生成两个分镜之间的过渡视频（使用首尾关键帧）。

## 核心要求

1. **提示词必须是英文**
2. **使用 Veo 3.1 五部分公式**：
   - [Cinematography] 摄影：镜头运动、构图、焦距
   - [Subject] 主体：主要角色或焦点
   - [Action] 动作：主体在做什么
   - [Context] 环境：背景和环境元素
   - [Style & Ambiance] 风格氛围：美学、情绪、光线

3. **摄影词汇库**（根据场景选择合适的）：
   - 镜头运动: dolly shot, tracking shot, crane shot, aerial view, slow pan, POV shot, arc shot, push in, pull back
   - 构图: wide shot, medium shot, close-up, extreme close-up, two-shot, over-the-shoulder, low angle, high angle
   - 焦距: shallow depth of field, deep focus, wide-angle lens, telephoto lens, rack focus, soft focus

4. **音频指令格式**（重要！）：
   - **禁止背景音乐**: 严格禁止任何背景音乐(BGM)、配乐、音乐主题、旋律、节奏音乐等
   - **只允许物理音效和环境音**: 仅包含真实的物理声音和环境声音
   - 对话：如果是中文对话,使用 'Character says in Chinese "对话内容"' 格式(语言类型在对话内容前面);如果是英文对话,直接使用 'Character says "dialogue content"'
   - 物理音效：使用 'SFX:' 前缀，例如 'SFX: footsteps on wooden floor', 'SFX: door creaking open', 'SFX: thunder cracks in the distance', 'SFX: sword clashing', 'SFX: glass breaking', 'SFX: heavy breathing', 'SFX: rain drops on window'
   - 环境音：使用 'Ambient noise:' 前缀，例如 'Ambient noise: quiet hum of city traffic', 'Ambient noise: wind rustling through trees', 'Ambient noise: distant crowd murmur', 'Ambient noise: quiet room tone'
   - **音频约束**: NO background music, NO BGM, NO musical score, NO soundtrack, NO melody, NO rhythmic music

5. **字幕规范**（如果有对话）：
   - **位置**: Bottom center of frame, leaving space from bottom edge
   - **字体**: Clean, bold sans-serif font (similar to Arial or Helvetica)
   - **文字颜色**: White text with black outline/stroke for maximum visibility
   - **背景**: Semi-transparent black bar behind text (opacity ~70%)
   - **大小**: Medium size, easily readable without dominating the frame
   - **对齐**: Center-aligned
   - **时机**: Subtitles appear synchronized with dialogue delivery
   - **语言**: Display Chinese characters exactly as provided in dialogue
   - **格式**: Each line of dialogue should have its own subtitle
   - **持续时间**: Subtitle remains visible for the duration of the spoken dialogue

6. **风格与氛围**：
   - 光线：natural light, golden hour, soft window light, dramatic shadows, volumetric light rays, harsh fluorescent
   - 情绪：melancholic, tense, joyful, mysterious, contemplative, energetic, serene
   - 美学：cinematic, moody, vibrant, noir, retro, contemporary

7. **角色名称保护**：
   - **角色名称必须与输入完全一致，不允许翻译、音译或修改**
   - 例如：输入是"李明"，输出也必须是"李明"，不能变成"Li Ming"

8. **只输出提示词本身**，不要包含任何解释、标记或分段标题

---

## 两个分镜的描述

{combined_text}

---

## 示例参考

**重要：所有示例中的角色名称都保持原始中文形式！**

### 示例1：对话场景 - 镜头推进过渡

输入：
分镜1: 特写，李明坐在办公桌前，表情严肃
对话: "这个项目必须在周五前完成"
角色: 李明
分镜2: 中景，王芳站起身，面露难色
对话: "时间太紧了，我需要更多人手"
角色: 王芳

输出：
Smooth dolly shot transition with Chinese dialogue and subtitles. Close-up of 李明 at office desk with serious expression, he says in Chinese "这个项目必须在周五前完成" with firm tone. Subtitle appears at bottom center: white bold text "这个项目必须在周五前完成" with black outline on semi-transparent black bar. Camera slowly pulls back and pans right, revealing the modern office interior with soft overhead fluorescent lighting. 王芳 comes into frame in medium shot, standing up from her chair with worried expression, she responds in Chinese "时间太紧了，我需要更多人手". Subtitle updates: white bold text "时间太紧了，我需要更多人手" with black outline on semi-transparent black bar. Ambient noise: quiet office atmosphere with subtle keyboard typing, distant phone ringing. Cinematic color grading with cool blue tones. Professional cinematography creating seamless narrative flow.

### 示例2：动作场景 - 跟踪镜头

输入：
分镜1: 全景，张伟在街道上奔跑
对话: 无
角色: 张伟
分镜2: 特写，张伟停下脚步，气喘吁吁
对话: "终于甩掉他们了"
角色: 张伟

输出：
Dynamic tracking shot with Chinese dialogue and subtitles. Wide shot of 张伟 sprinting through urban street at dusk, his footsteps echoing on wet pavement. Camera follows with smooth tracking movement, maintaining consistent framing. Gradual push in to close-up as he slows down and stops, breathing heavily with relief. He catches his breath and says in Chinese "终于甩掉他们了" with exhausted voice. Subtitle appears at bottom center: white bold text "终于甩掉他们了" with black outline on semi-transparent black bar. SFX: heavy breathing, footsteps on pavement, distant car horn. Ambient noise: city traffic in background. Natural lighting with slight motion blur during running. Moody cinematic aesthetic with desaturated colors.

### 示例3：情感场景 - 缓慢推进

输入：
分镜1: 中景，小雨坐在窗边，望向窗外
对话: 无
角色: 小雨
分镜2: 特写，小雨的眼中泛起泪光
对话: "我真的很想念你"
角色: 小雨

输出：
Intimate slow push in with Chinese dialogue and subtitles. Medium shot of 小雨 sitting by rain-streaked window, gazing outside with melancholic expression. Soft natural window light illuminating her face with gentle shadows. Camera slowly pushes in for emotional close-up, revealing tears welling up in her eyes. She whispers in Chinese "我真的很想念你" with trembling, emotional voice. Subtitle appears at bottom center: white bold text "我真的很想念你" with black outline on semi-transparent black bar. SFX: gentle rain drops on window glass. Ambient noise: distant thunder, quiet room tone. Shallow depth of field with soft bokeh in background. Contemplative mood with warm, muted color palette. Cinematic film photography aesthetic.

### 示例4：环境过渡 - 摇臂镜头

输入：
分镜1: 全景，城堡外的荒野，暴风雨
对话: 无
角色: 无
分镜2: 中景，城堡大厅内，壁炉火光
对话: 无
角色: 无

输出：
Dramatic crane shot transition. Wide establishing shot of desolate wilderness outside ancient castle, storm clouds gathering overhead with lightning flashing in distance. Camera performs sweeping crane movement, rising up and moving toward castle entrance. Smooth transition to medium shot of grand hall interior, warm fireplace light flickering on stone walls. SFX: howling wind, thunder rumbling, crackling fire. Ambient noise: storm outside transitioning to quiet interior ambience. High contrast lighting from dark exterior to warm interior glow. Epic cinematic scope with rich atmospheric detail. Moody, ominous aesthetic shifting to warm refuge.

---

现在请为上述两个分镜生成过渡视频提示词：
```

---

## 使用说明

### 1. Prompt调用方式

所有Prompt都通过 `MoviePromptTemplates` 类的静态方法获取:

```python
from src.services.movie_prompts import MoviePromptTemplates

# 场景提取
scene_prompt = MoviePromptTemplates.get_scene_extraction_prompt(
    characters='["角色1", "角色2"]',
    text="章节内容..."
)

# 分镜提取
shot_prompt = MoviePromptTemplates.get_shot_extraction_prompt(
    characters='["角色1", "角色2"]',
    scene="场景描述..."
)

# 场景图生成
scene_image_prompt = MoviePromptTemplates.get_scene_image_prompt(
    scene_description="场景描述..."
)

# 过渡视频
transition_prompt = MoviePromptTemplates.get_transition_video_prompt(
    combined_text="分镜1...\n分镜2..."
)
```

### 2. LLM调用配置

#### JSON输出模式
角色提取、场景提取、分镜提取都使用JSON输出模式:

```python
response = await llm_provider.completions(
    model=model,
    messages=[
        {"role": "system", "content": "你是一个专业的XXX。只输出JSON。"},
        {"role": "user", "content": prompt},
    ],
    response_format={"type": "json_object"}
)
```

#### 普通文本模式
过渡视频Prompt生成使用普通文本模式:

```python
response = await llm_provider.completions(
    model=model,
    messages=[
        {"role": "system", "content": "你是一个专业的电影视频提示词生成专家。"},
        {"role": "user", "content": prompt},
    ]
)
```

### 3. 响应处理

#### JSON响应清理
```python
content = response.choices[0].message.content.strip()

# 清理可能的代码块标记
if content.startswith("```json"):
    content = content[7:-3].strip()
elif content.startswith("```"):
    content = content[3:-3].strip()

data = json.loads(content)
```

#### 文本响应
```python
prompt = response.choices[0].message.content.strip()
```

---

## Prompt设计原则

### 1. 结构化输出
- 使用JSON格式确保输出可解析
- 明确字段名称和数据类型
- 提供输出示例

### 2. 约束条件
- 明确禁止的行为(如创造新角色)
- 强调必须遵守的规则
- 使用【强约束规则】等醒目标记

### 3. 详细说明
- 提供字段的详细写作规范
- 给出正确和错误的示例
- 说明信息密度要求

### 4. 一致性保证
- 角色名称格式统一
- 视觉描述风格一致
- 术语使用标准化

### 5. 可扩展性
- 支持自定义参数
- 允许覆盖默认行为
- 模板化设计便于维护

---

## 常见问题

### Q1: 为什么角色名称要包含英文?
A: 使用"中文名 (英文名)"格式可以:
- 在图像生成时提供英文参考
- 保持中文显示的一致性
- 便于国际化

### Q2: 为什么场景图要求无人物?
A: 场景图是环境建立镜头(Establishing Shot),用于:
- 展示场景的整体氛围
- 避免角色一致性问题
- 作为场景的视觉参考

### Q3: 关键帧和过渡视频的关系?
A: 
- 关键帧是静态图片,代表分镜的瞬间
- 过渡视频使用前后关键帧作为首尾帧
- AI模型生成中间帧实现平滑过渡

### Q4: 如何调整Prompt效果?
A:
- 修改 `movie_prompts.py` 中的模板
- 使用自定义提示词覆盖默认生成
- 调整LLM模型参数(temperature等)

### Q5: Prompt token限制怎么处理?
A:
- 角色提取限制章节内容为5000字符
- 场景和分镜提取按需分批处理
- 使用更大上下文窗口的模型

---

## 版本历史

- **v1.0** (2025-12): 初始版本,包含所有6个主要Prompt模板
- 支持角色提取、场景提取、分镜提取
- 支持场景图生成、角色三视图生成
- 支持过渡视频Prompt生成

---

## 相关文档

- [电影生成流程完整文档](./movie_generation_workflow.md)
- [API使用文档](./api_documentation.md)
- [最佳实践指南](./best_practices.md)
