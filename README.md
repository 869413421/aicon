# AICON

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/deploy-docker-2496ED.svg)](https://www.docker.com/)

AICON 是一套面向 AI 内容创作的全栈工作台，覆盖从文本理解、提示词组织、图片与视频生成，到素材管理和内容分发的完整流程，适用于 AI 电影、图文说、剧情短视频和可视化创作工作流等场景。

**自然语言驱动的开源无限画布 AI 工作流与 Agent 协作工作台**，让剧本、角色、分镜、关键帧与视频节点在同一画布协作。

在线站点：[https://aicon-studio.com/](https://aicon-studio.com/)

技术栈：`FastAPI`、`Vue 3`、`PostgreSQL`、`Redis`、`Celery`、`MinIO`

> 说明：本人目前在广州地区求职中，具备丰富的 AI 应用开发经验，包括 Agent、RAG 等方向，欢迎相关技术岗位与合作机会交流。

## Atlas Cloud（一套 OpenAI 兼容 API 跑通整条创作链路）

<p align="center">
  <a href="https://www.atlascloud.ai/?utm_source=github&utm_medium=link&utm_campaign=ai-moive-studio">
    <img src="docs/media/atlas-cloud-logo.png" alt="Atlas Cloud" width="200">
  </a>
</p>

> 🎁 **[Atlas Cloud](https://www.atlascloud.ai/?utm_source=github&utm_medium=link&utm_campaign=ai-moive-studio)** 是一个全模态 AI 推理平台，用一套 OpenAI 兼容 API 同时覆盖 AICON「剧本拆解 → 分镜提示词 → 图片 → 配音/视频」的整条创作链路：LLM（DeepSeek、Qwen、GLM、Kimi、MiniMax…）做文本理解与提示词组织，图像/视频生成（Seedream、Seedance、Kling、Wan、Nano Banana…）做关键帧与过渡视频，连一次即可，无需逐家厂商分别对接。
>
> 💡 LLM 预算友好：[coding plan](https://www.atlascloud.ai/console/coding-plan) · 全量模型：[atlascloud.ai/models](https://www.atlascloud.ai/models)

在 AICON 里使用：「API 密钥管理」中新增一个密钥，**服务提供商选 `Atlas Cloud`**，填入你的 Atlas API Key 即可（默认 `base_url` 已指向 `https://api.atlascloud.ai/v1`）。代码层对应内置的 `atlascloud` provider（OpenAI 兼容透传）。

```env
# Atlas Cloud（OpenAI 兼容）—— 仅作配置示例，API Key 在 AICON 界面里填，不要硬编码
ATLASCLOUD_API_BASE=https://api.atlascloud.ai/v1
ATLASCLOUD_API_KEY=<your-atlascloud-api-key>
# LLM 默认（带推理，调用时给足 max_tokens >= 512）
ATLASCLOUD_LLM_MODEL=deepseek-ai/deepseek-v4-pro
# 图像默认
ATLASCLOUD_IMAGE_MODEL=openai/gpt-image-2/text-to-image
# 视频默认
ATLASCLOUD_VIDEO_MODEL=bytedance/seedance-2.0/text-to-video
```

`deepseek-ai/deepseek-v4-pro` 是带推理（reasoning）的模型，调用时请给足 `max_tokens`（建议 >= 512），否则 token 可能先耗在思维链上，出现 `finish_reason=length` 且 `content` 为空。

<details>
<summary>Atlas Cloud 全部对话模型（59 个，与官网 /zh/models/list/llm 一致）</summary>

- Anthropic (Claude)：`anthropic/claude-haiku-4.5-20251001`, `anthropic/claude-opus-4.8`, `anthropic/claude-sonnet-4.6`
- OpenAI (GPT)：`openai/gpt-5.4`, `openai/gpt-5.5`
- Google (Gemini)：`google/gemini-3.1-flash-lite`, `google/gemini-3.1-pro-preview`, `google/gemini-3.5-flash`
- 阿里 Qwen：`qwen/qwen2.5-7b-instruct`, `Qwen/Qwen3-235B-A22B-Instruct-2507`, `qwen/qwen3-235b-a22b-thinking-2507`, `qwen/qwen3-30b-a3b`, `Qwen/Qwen3-30B-A3B-Instruct-2507`, `qwen/qwen3-30b-a3b-thinking-2507`, `qwen/qwen3-32b`, `qwen/qwen3-8b`, `Qwen/Qwen3-Coder`, `qwen/qwen3-coder-next`, `qwen/qwen3-max-2026-01-23`, `Qwen/Qwen3-Next-80B-A3B-Instruct`, `Qwen/Qwen3-Next-80B-A3B-Thinking`, `Qwen/Qwen3-VL-235B-A22B-Instruct`, `qwen/qwen3-vl-235b-a22b-thinking`, `qwen/qwen3-vl-30b-a3b-instruct`, `qwen/qwen3-vl-30b-a3b-thinking`, `qwen/qwen3-vl-8b-instruct`, `qwen/qwen3.5-122b-a10b`, `qwen/qwen3.5-27b`, `qwen/qwen3.5-35b-a3b`, `qwen/qwen3.5-397b-a17b`, `qwen/qwen3.6-35b-a3b`, `qwen/qwen3.6-plus`
- DeepSeek：`deepseek-ai/deepseek-ocr`, `deepseek-ai/deepseek-r1-0528`, `deepseek-ai/DeepSeek-V3-0324`, `deepseek-ai/DeepSeek-V3.1`, `deepseek-ai/DeepSeek-V3.1-Terminus`, `deepseek-ai/deepseek-v3.2`, `deepseek-ai/DeepSeek-V3.2-Exp`, `deepseek-ai/deepseek-v4-flash`, `deepseek-ai/deepseek-v4-pro`
- Moonshot (Kimi)：`moonshotai/Kimi-K2-Instruct`, `moonshotai/Kimi-K2-Instruct-0905`, `moonshotai/Kimi-K2-Thinking`, `moonshotai/kimi-k2.5`, `moonshotai/kimi-k2.6`
- 智谱 GLM：`zai-org/GLM-4.6`, `zai-org/glm-4.7`, `zai-org/glm-5`, `zai-org/glm-5-turbo`, `zai-org/glm-5.1`, `zai-org/glm-5v-turbo`
- MiniMax：`MiniMaxAI/MiniMax-M2`, `minimaxai/minimax-m2.1`, `minimaxai/minimax-m2.5`, `minimaxai/minimax-m2.7`
- xAI：`xai/grok-4.3`
- 快手 KAT：`kwaipilot/kat-coder-pro-v2`
- 其他：`owl`

图像 / 视频默认模型：文生图 `openai/gpt-image-2/text-to-image`、文生视频 `bytedance/seedance-2.0/text-to-video`，完整清单见 [atlascloud.ai/models](https://www.atlascloud.ai/models)。

</details>

## 目录

- [项目概览](#项目概览)
- [核心功能](#核心功能)
- [适用场景](#适用场景)
- [功能截图](#功能截图)
- [Star 趋势](#star-趋势)
- [演示](#演示)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [更新日志](#更新日志)
- [交流与支持](#交流与支持)
- [仓库结构](#仓库结构)
- [相关文档](#相关文档)
- [License](#license)

## 项目概览

AICON 当前主要包含以下能力：

- `Movie Studio`：将长文本拆解为角色、场景、分镜、关键帧和过渡视频，形成完整的 AI 电影制作链路。
- `Picture Narration`：面向图文说和短视频配图场景，支持章节拆分、提示词生成、配图生成、语音合成与渲染。
- `Canvas`：将文本、图片、视频节点放在同一画布中编辑，通过节点引用、连线和 Agent 助手组织生成上下文。
- `Distribution`：支持 Bilibili 等平台的自动化发布与内容分发。

项目特征：

- 统一工作流：从文本到图片、视频、配音、发布尽量在一套系统内完成。
- 可扩展供应商：支持自定义兼容 Base URL，可替换模型供应商。
- 异步任务架构：适合长链路生成任务、批量任务与媒体处理任务。
- 画布式创作：适合组织复杂 prompt、参考图和多轮生成结果。
- Agent 协作工作流：支持在画布侧边助手中按视频工作流创建节点链路，并由用户手动触发生成。

## 核心功能

### Movie Studio

面向长文本到视频的自动化生产流程：

- 智能解析文本，提取角色、场景与分镜结构。
- 基于角色参考图维持角色一致性，降低跨镜头“换脸”问题。
- 支持关键帧、过渡视频、背景音乐与音效合成。
- 输出适合主流视频平台发布的完整内容资产。

### Picture Narration

面向短视频配图和图文说的批量生成能力：

- 自动识别章节与段落结构。
- 为段落生成匹配的视觉提示词与构图描述。
- 并发生成图片、语音与字幕素材。
- 组合为可直接发布的视频内容。

### Canvas

面向创意编排和工作流组织的可视化画布：

- 支持文本、图片、视频节点自由排布与编辑。
- 支持通过连线建立依赖关系，并在生成时引用上游内容。
- 支持引用图片、上传参考图和叠加风格参考。
- 支持查看生成历史并回切历史版本。
- 打开画布时返回轻量快照，兼顾大画布加载和编辑体验。
- 内置 `Canvas Assistant`，可根据一句创意或剧本想法引导用户从剧本、角色三视图、分镜、关键帧到视频节点逐步搭建工作流。
- 工作流助手当前默认**只创建节点与连线**，不会自动提交角色三视图、关键帧、视频生成任务，后续生成由用户在画布中手动触发。
- 关键帧预备节点会自动带入对应角色三视图引用，便于后续保持角色一致性。
- 支持框选多个节点并一次性批量删除，删除前带确认环节；批量删除会同时清理关联连线。
- 图片节点和视频节点在新建时会自动填入默认 API Key 与默认模型，减少首次配置成本。

### Distribution

面向发布环节的自动化能力：

- 支持接入 Bilibili API。
- 支持上传视频、生成标题摘要与标签建议。

## 适用场景

- 小说、剧本、设定集等长文本的影视化生成
- AI 图文说、解说视频、剧情短视频的批量制作
- 角色一致性要求较高的图像与视频生成
- 提示词编排、参考图管理、多版本对比的创作流程

## 功能截图

### 无限画布Agent
![无限画布](docs/media/agent.png)

### 角色管理
![角色管理](docs/media/角色管理.png)

### 场景图生成
![场景图生成](docs/media/场景图生成.png)

### 关键帧生成
![关键帧生成](docs/media/关键帧生成.png)

### 过渡视频
![过渡视频](docs/media/过度视频.png)

### 发布管理
![发布管理](docs/media/发布管理.png)

## Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=869413421/aicon&type=Date)](https://www.star-history.com/#869413421/aicon&Date)

## 演示

示例视频：

- [《静默战争》演示](https://www.bilibili.com/video/BV1DpvaB8EDE/?vd_source=2da8614f110387a6fe068f446424c748)
- [《艾尔登法环真人版预告》演示](https://www.bilibili.com/video/BV1w3igBpEXo)

## 快速开始

推荐使用 Docker 部署。

```bash
git clone https://github.com/869413421/aicon.git
cd aicon

cp .env.production.example .env.production
# 编辑 .env.production，填写数据库、Redis、JWT、MinIO 等配置

docker-compose -f docker-compose.prod.yml up -d
```

默认访问地址：

- 前端：`http://localhost`
- 后端 API：`http://localhost:8000`

更多部署细节见 [docs/docker-deployment-guide.md](docs/docker-deployment-guide.md)。

如需分别查看前后端说明，可进一步阅读：

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

## 使用说明

### 1. 获取 API Key

系统支持多种模型供应商；如果你希望直接体验项目当前默认兼容链路，可以使用：

- 注册地址：[https://api.aiconapi.me/](https://api.aiconapi.me/)
- 注册并购买额度后，在令牌页面创建 API Key
- 建议按需购买

### 2. 配置系统 API Key

进入系统后台，在“API 密钥管理”页面新增密钥：

- 供应商：选择 `自定义`
- API 密钥：填写你自己的令牌
- Base URL：默认值为 `https://api.aiconapi.me/v1`

注意：

- Base URL 结尾不要带斜杠，例如不要写成 `https://api.aiconapi.me/v1/`

### 3. 关于中转站

`https://api.aiconapi.me/v1` 是项目作者自部署的大模型兼容中转站，目标是提供长期可用、相对低价的默认接入方式，并非强制绑定。

如果你已有自己的兼容网关、代理层或模型供应商，可以直接修改 Base URL，也可以进一步调整代码中的供应商兼容逻辑。

相关代码位置：

- 后端供应商工厂：`backend/src/services/provider/factory.py`
- 后端自定义供应商封装：`backend/src/services/provider/custom_provider.py`
- 前端 API 密钥管理页：`frontend/src/views/APIKeys.vue`
- 前端设置页 API 密钥面板：`frontend/src/views/settings/APIKeysSettings.vue`

### 4. 开始创作

基本流程如下：

1. 新建项目
2. 导入文本，建议按章节导入
3. 进入项目详情页，使用 `Movie Studio` 或 `Canvas`
4. 按角色提取、场景提取、分镜生成、素材生成和视频合成的顺序推进

## 更新日志

### 2026-04-03

- 新增 `Canvas` 无限画布工作台
- 支持节点引用生成
- 支持生成历史回看与切换
- JWT TOKEN 默认有效期调整为 `7` 天，即 `10080` 分钟
- `custom` 供应商默认 Base URL 调整为 `https://api.aiconapi.me/v1`

### 2026-04-06

- 新增 `Canvas Assistant` 画布侧边助手引导文案与流式状态优化
- 新增工作流辅助建链：可按剧本自动创建角色三视图、分镜、关键帧、视频节点及连线
- 工作流模式调整为“只创建节点，不自动提交生成任务”，后续生成由用户手动触发
- 关键帧预备节点自动注入角色三视图引用
- 画布支持 `Shift + 拖拽` 框选多节点，并支持批量删除确认
- 新建图片/视频节点时自动带默认 API Key 与默认模型

### 2026-02-28

- 新增 `gemini-3.1-flash-image-preview` 图像模型支持
- 新增 `gemini-3.1-pro` 文本模型支持

### 2026-01-23

- 发布 Docker 镜像 `v1.1.0`
- 修复模型列表加载问题
- `custom` 供应商新增一系列 Veo 3.1 视频模型支持

### 2026-01-15

- 在线站点上线内测
- 新增角色参考图能力
- 新增 `VEO3.1 4K` 模型支持
- 补充项目文档与交流群说明

## 交流与支持

扫码加入 AICON 内测交流群，获取最新动态、功能更新与使用支持。

<img src="docs/media/qr.jpg" width="200" alt="AICON 内测交流群">

## 仓库结构

```text
aicon/
├── backend/     # FastAPI 后端、任务队列、数据模型
├── frontend/    # Vue 3 前端
├── docs/        # 部署与开发文档
└── README.md
```

## 相关文档

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [docs/docker-deployment-guide.md](docs/docker-deployment-guide.md)

## License

本项目采用 [Apache License 2.0](LICENSE)。
