# API Contracts: AICG内容分发平台

**Created**: 2025-11-06
**Purpose**: 定义API接口契约，确保前后端开发一致性
**Scope**: RESTful API + WebSocket实时通信

## API 版本策略

- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token (JWT)
- **API版本**: URL路径版本控制 (`/api/v1`, `/api/v2`)

## 核心API端点

### 1. 用户认证与管理 API

```yaml
# 用户注册
POST /api/v1/auth/register
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username: { type: string, minLength: 3, maxLength: 50 }
          email: { type: string, format: email }
          password: { type: string, minLength: 8, maxLength: 128 }
          display_name: { type: string, maxLength: 100, nullable: true }
        required: [username, email, password]
response:
  type: object
  properties:
    user: { $ref: "#/components/schemas/User" }
    access_token: { type: string }
    refresh_token: { type: string }
    token_type: { type: string, default: "bearer" }
    expires_in: { type: integer }

# 用户登录
POST /api/v1/auth/login
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username: { type: string }
          password: { type: string }
        required: [username, password]
response:
  type: object
  properties:
    user: { $ref: "#/components/schemas/User" }
    access_token: { type: string }
    refresh_token: { type: string }
    token_type: { type: string, default: "bearer" }
    expires_in: { type: integer }

# 刷新Token
POST /api/v1/auth/refresh
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          refresh_token: { type: string }
        required: [refresh_token]
response:
  type: object
  properties:
    access_token: { type: string }
    refresh_token: { type: string }
    expires_in: { type: integer }

# 用户登出
POST /api/v1/auth/logout
headers:
  Authorization: Bearer {token}
response:
  type: object
  properties:
    message: { type: string }

# 获取当前用户信息
GET /api/v1/auth/me
headers:
  Authorization: Bearer {token}
response:
  type: object
  properties:
    user: { $ref: "#/components/schemas/User" }

# 更新用户信息
PUT /api/v1/users/me
headers:
  Authorization: Bearer {token}
requestBody:
  type: object
  properties:
    display_name: { type: string, maxLength: 100 }
    avatar_url: { type: string, maxLength: 500 }
    preferences: { type: object }
    timezone: { type: string }
    language: { type: string }

# 修改密码
PUT /api/v1/users/me/password
headers:
  Authorization: Bearer {token}
requestBody:
  type: object
  properties:
    current_password: { type: string }
    new_password: { type: string, minLength: 8, maxLength: 128 }
  required: [current_password, new_password]

# 用户统计信息
GET /api/v1/users/me/stats
headers:
  Authorization: Bearer {token}
response:
  type: object
  properties:
    projects_count: { type: integer }
    total_words: { type: integer }
    generated_videos: { type: integer }
    published_videos: { type: integer }
    api_usage_this_month: { type: number }
    total_cost: { type: number }
```

### 2. 项目管理 API

```yaml
# 项目列表
GET /api/v1/projects
parameters:
  - name: page
    type: integer
    default: 1
    description: 页码
  - name: limit
    type: integer
    default: 20
    description: 每页数量
response:
  type: object
  properties:
    projects:
      type: array
      items: { $ref: "#/components/schemas/Project" }
    total: { type: integer }
    page: { type: integer }
    limit: { type: integer }

# 创建项目
POST /api/v1/projects
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          title: { type: string, maxLength: 200 }
          description: { type: string, maxLength: 1000 }
          file_id: { type: string }
        required: [title, file_id]

# 项目详情
GET /api/v1/projects/{project_id}
pathParameters:
  - name: project_id
    type: string
    required: true

# 删除项目
DELETE /api/v1/projects/{project_id}
```

### 2. 文件上传与处理 API

```yaml
# 文件上传
POST /api/v1/upload
requestBody:
  required: true
  content:
    multipart/form-data:
      schema:
        type: object
        properties:
          file:
            type: string
            format: binary
            description: 支持txt, md, docx, epub格式
response:
  type: object
  properties:
    file_id: { type: string }
    file_name: { type: string }
    file_size: { type: integer }
    file_type: { type: string }
    upload_url: { type: string }

# 文档解析状态
GET /api/v1/projects/{project_id}/parse-status
response:
  type: object
  properties:
    status: { type: string, enum: ["pending", "processing", "completed", "failed"] }
    progress: { type: integer, minimum: 0, maximum: 100 }
    message: { type: string }
    chapters_found: { type: integer }
```

### 3. 章节管理 API

```yaml
# 章节列表
GET /api/v1/projects/{project_id}/chapters
queryParameters:
  - name: status
    type: string
    enum: ["all", "pending", "confirmed", "processing"]
    default: "all"

# 章节详情
GET /api/v1/chapters/{chapter_id}
response:
  type: object
  properties:
    id: { type: string }
    title: { type: string }
    content: { type: string }
    word_count: { type: integer }
    status: { type: string }
    created_at: { type: string, format: date-time }

# 章节解析（按需）
POST /api/v1/chapters/{chapter_id}/parse
response:
  type: object
  properties:
    paragraphs:
      type: array
      items: { $ref: "#/components/schemas/Paragraph" }
    sentences:
      type: array
      items: { $ref: "#/components/schemas/Sentence" }

# 章节确认
PUT /api/v1/chapters/{chapter_id}/confirm
requestBody:
  type: object
  properties:
    confirmed_paragraphs:
      type: array
      items:
        type: object
        properties:
          id: { type: string }
          content: { type: string }
          action: { type: string, enum: ["keep", "edit", "delete", "ignore"] }
```

### 4. 句子管理 API

```yaml
# 句子详情
GET /api/v1/sentences/{sentence_id}
response:
  type: object
  properties:
    id: { type: string }
    content: { type: string }
    paragraph_id: { type: string }
    order_index: { type: integer }
    image_url: { type: string, nullable: true }
    audio_url: { type: string, nullable: true }
    start_time: { type: number, nullable: true }
    end_time: { type: number, nullable: true }
    status: { type: string }

# 句子编辑
PUT /api/v1/sentences/{sentence_id}
requestBody:
  type: object
  properties:
    content: { type: string }
    image_prompt: { type: string }
    voice_settings: { type: object }
```

### 5. 视频生成 API

```yaml
# 批量生成启动
POST /api/v1/generation/start
requestBody:
  type: object
  properties:
    chapter_ids:
      type: array
      items: { type: string }
    api_config_id: { type: string }
    generation_settings:
      type: object
      properties:
        video_style: { type: string }
        voice_type: { type: string }
        background_music: { type: boolean }

# 生成队列状态
GET /api/v1/generation/queue
response:
  type: object
  properties:
    active_tasks: { type: array, items: { $ref: "#/components/schemas/GenerationTask" } }
    pending_tasks: { type: array }
    completed_count: { type: integer }
    failed_count: { type: integer }

# 任务控制
POST /api/v1/generation/tasks/{task_id}/control
requestBody:
  type: object
  properties:
    action: { type: string, enum: ["pause", "resume", "cancel", "retry"] }

# 生成进度
GET /api/v1/generation/tasks/{task_id}/progress
response:
  type: object
  properties:
    task_id: { type: string }
    status: { type: string }
    progress: { type: number }
    current_step: { type: string }
    estimated_completion: { type: string }
    error_message: { type: string, nullable: true }
```

### 6. 时间轴与字幕 API

```yaml
# 时间轴生成
POST /api/v1/chapters/{chapter_id}/timeline/generate
response:
  type: object
  properties:
    timeline_id: { type: string }
    sentences_timing:
      type: array
      items:
        type: object
        properties:
          sentence_id: { type: string }
          start_time: { type: number }
          end_time: { type: number }
          duration: { type: number }

# 字幕文件下载
GET /api/v1/chapters/{chapter_id}/subtitles
queryParameters:
  - name: format
    type: string
    enum: ["srt", "vtt", "ass"]
    default: "srt"
response:
  type: string
  format: binary
  description: 字幕文件内容

# 字幕样式设置
PUT /api/v1/chapters/{chapter_id}/subtitles/style
requestBody:
  type: object
  properties:
    font_family: { type: string }
    font_size: { type: integer }
    font_color: { type: string }
    background_color: { type: string }
    position: { type: string }
```

### 7. 视频合成 API

```yaml
# 视频合成启动
POST /api/v1/chapters/{chapter_id}/synthesize
requestBody:
  type: object
  properties:
    resolution: { type: string, enum: ["720p", "1080p", "4k"], default: "1080p" }
    fps: { type: integer, default: 30 }
    subtitle_style: { type: object }
    background_music: { type: string, nullable: true }

# 视频下载
GET /api/v1/videos/{video_id}/download
queryParameters:
  - name: quality
    type: string
    enum: ["low", "medium", "high"]
    default: "medium"
response:
  type: string
  format: binary
  description: 视频文件内容

# 视频预览
GET /api/v1/videos/{video_id}/preview
queryParameters:
  - name: timestamp
    type: number
    description: 预览时间点（秒）
response:
  type: string
  format: binary
  description: 预览帧图片
```

### 8. 内容发布 API

```yaml
# 平台账号绑定
POST /api/v1/publications/platforms/{platform}/bind
pathParameters:
  - name: platform
    type: string
    enum: ["bilibili", "youtube"]
requestBody:
  type: object
  properties:
    auth_code: { type: string }
    redirect_uri: { type: string }

# 发布视频
POST /api/v1/publications
requestBody:
  type: object
  properties:
    video_ids:
      type: array
      items: { type: string }
    platforms:
      type: array
      items:
        type: object
        properties:
          platform: { type: string }
          title: { type: string }
          description: { type: string }
          tags: { type: array, items: { type: string } }
          visibility: { type: string }
          scheduled_time: { type: string, nullable: true }

# 发布记录
GET /api/v1/publications/records
response:
  type: object
  properties:
    records:
      type: array
      items: { $ref: "#/components/schemas/PublicationRecord" }
    total: { type: integer }
```

### 10. API配置管理

```yaml
# API密钥列表
GET /api/v1/api-configs
headers:
  Authorization: Bearer {token}
response:
  type: array
  items: { $ref: "#/components/schemas/APIConfig" }

# 添加API配置
POST /api/v1/api-configs
headers:
  Authorization: Bearer {token}
requestBody:
  type: object
  properties:
    name: { type: string, maxLength: 100 }
    provider: { type: string, enum: ["volcengine", "openai", "azure", "google", "baidu", "alibaba", "custom"] }
    service_type: { type: string, enum: ["image_generation", "audio_generation", "translation", "video_synthesis"] }
    api_key: { type: string }
    api_secret: { type: string, nullable: true }
    endpoint: { type: string }
    region: { type: string }
    monthly_limit: { type: integer }
    daily_limit: { type: integer }
    rate_limit: { type: integer }
    is_active: { type: boolean, default: true }
    is_default: { type: boolean, default: false }
    config_params: { type: object }
  required: [name, provider, service_type, api_key]

# 更新API配置
PUT /api/v1/api-configs/{config_id}
headers:
  Authorization: Bearer {token}
requestBody:
  type: object
  properties:
    name: { type: string }
    is_active: { type: boolean }
    is_default: { type: boolean }
    monthly_limit: { type: integer }
    config_params: { type: object }

# 删除API配置
DELETE /api/v1/api-configs/{config_id}
headers:
  Authorization: Bearer {token}

# 验证API配置
POST /api/v1/api-configs/{config_id}/verify
headers:
  Authorization: Bearer {token}
response:
  type: object
  properties:
    is_valid: { type: boolean }
    test_result: { type: object }
    error_message: { type: string, nullable: true }

# 用量统计
GET /api/v1/api-configs/{config_id}/usage
headers:
  Authorization: Bearer {token}
queryParameters:
  - name: start_date
    type: string
    format: date
  - name: end_date
    type: string
    format: date
response:
  type: object
  properties:
    total_calls: { type: integer }
    success_calls: { type: integer }
    failed_calls: { type: integer }
    cost_estimate: { type: number }
    current_usage: { type: integer }
    daily_usage:
      type: array
      items:
        type: object
        properties:
          date: { type: string }
          calls: { type: integer }
          cost: { type: number }
          success_rate: { type: number }

# 所有API配置汇总统计
GET /api/v1/api-configs/summary
headers:
  Authorization: Bearer {token}
response:
  type: object
  properties:
    total_configs: { type: integer }
    active_configs: { type: integer }
    total_cost_this_month: { type: number }
    total_calls_this_month: { type: integer }
    by_provider:
      type: array
      items:
        type: object
        properties:
          provider: { type: string }
          configs_count: { type: integer }
          calls_count: { type: integer }
          cost: { type: number }
```

## WebSocket 实时通信

### 连接端点

```
ws://localhost:8000/ws/progress/{task_id}
ws://localhost:8000/ws/notifications/{user_id}
```

### 消息格式

```javascript
// 进度更新消息
const ProgressMessage = {
  type: "progress",
  task_id: "string",
  progress: "number",
  current_step: "string",
  message: "string (optional)"
};

// 状态变更消息
const StatusMessage = {
  type: "status",
  task_id: "string",
  status: ["pending", "processing", "completed", "failed"],
  error: "string (optional)"
};

// 通知消息
const NotificationMessage = {
  type: "notification",
  title: "string",
  message: "string",
  level: ["info", "warning", "error", "success"],
  timestamp: "string",
  action_url: "string (optional)"
};
```

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2025-11-06T10:30:00Z"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "title",
        "message": "标题不能为空"
      }
    ]
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```

## 状态码规范

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突
- `422 Unprocessable Entity`: 业务逻辑错误
- `429 Too Many Requests`: 频率限制
- `500 Internal Server Error`: 服务器内部错误

## 分页参数

```javascript
// 分页参数
const PaginationParams = {
  page: "number (optional)",      // 页码，从1开始
  limit: "number (optional)",     // 每页数量，默认20，最大100
  sort: "string (optional)",      // 排序字段
  order: ["asc", "desc"]          // 排序方向
};

// 分页响应
const PaginationResponse = {
  data: "Array",
  pagination: {
    page: "number",
    limit: "number",
    total: "number",
    total_pages: "number",
    has_next: "boolean",
    has_prev: "boolean"
  }
};
```

## 数据模型定义

### User 模型

```yaml
User:
  type: object
  properties:
    id: { type: string }
    username: { type: string }
    email: { type: string }
    display_name: { type: string, nullable: true }
    avatar_url: { type: string, nullable: true }
    is_active: { type: boolean }
    is_verified: { type: boolean }
    last_login: { type: string, format: date-time, nullable: true }
    preferences: { type: object, nullable: true }
    timezone: { type: string, default: "Asia/Shanghai" }
    language: { type: string, default: "zh-CN" }
    created_at: { type: string, format: date-time }
    updated_at: { type: string, format: date-time }
```

### Project 模型

```yaml
Project:
  type: object
  properties:
    id: { type: string }
    title: { type: string }
    description: { type: string }
    file_name: { type: string }
    file_size: { type: integer }
    word_count: { type: integer }
    chapter_count: { type: integer }
    status: { type: string, enum: ["uploaded", "parsing", "parsed", "generating", "completed"] }
    created_at: { type: string, format: date-time }
    updated_at: { type: string, format: date-time }
```

### Chapter 模型

```yaml
Chapter:
  type: object
  properties:
    id: { type: string }
    project_id: { type: string }
    title: { type: string }
    content: { type: string }
    word_count: { type: integer }
    paragraph_count: { type: integer }
    status: { type: string, enum: ["pending", "confirmed", "processing", "completed"] }
    created_at: { type: string, format: date-time }
```

### Paragraph 模型

```yaml
Paragraph:
  type: object
  properties:
    id: { type: string }
    chapter_id: { type: string }
    content: { type: string }
    order_index: { type: integer }
    sentence_count: { type: integer }
    action: { type: string, enum: ["keep", "edit", "delete", "ignore"], default: "keep" }
    is_confirmed: { type: boolean, default: false }
```

### Sentence 模型

```yaml
Sentence:
  type: object
  properties:
    id: { type: string }
    paragraph_id: { type: string }
    content: { type: string }
    order_index: { type: integer }
    image_url: { type: string, nullable: true }
    audio_url: { type: string, nullable: true }
    start_time: { type: number, nullable: true }
    end_time: { type: number, nullable: true }
    duration: { type: number, nullable: true }
    status: { type: string, enum: ["pending", "processing", "completed", "failed"] }
    image_prompt: { type: string, nullable: true }
    voice_settings: { type: object, nullable: true }
```

### GenerationTask 模型

```yaml
GenerationTask:
  type: object
  properties:
    id: { type: string }
    chapter_id: { type: string }
    api_config_id: { type: string }
    status: { type: string, enum: ["pending", "processing", "paused", "completed", "failed", "cancelled"] }
    progress: { type: integer, minimum: 0, maximum: 100 }
    current_step: { type: string }
    total_sentences: { type: integer }
    completed_sentences: { type: integer }
    failed_sentences: { type: integer }
    estimated_completion: { type: string, nullable: true }
    error_message: { type: string, nullable: true }
    created_at: { type: string, format: date-time }
    started_at: { type: string, format: date-time, nullable: true }
    completed_at: { type: string, format: date-time, nullable: true }
```

### PublicationRecord 模型

```yaml
PublicationRecord:
  type: object
  properties:
    id: { type: string }
    video_id: { type: string }
    platform: { type: string, enum: ["bilibili", "youtube"] }
    platform_video_id: { type: string, nullable: true }
    title: { type: string }
    description: { type: string }
    status: { type: string, enum: ["pending", "publishing", "published", "failed"] }
    published_at: { type: string, format: date-time, nullable: true }
    error_message: { type: string, nullable: true }
    view_count: { type: integer, default: 0 }
    like_count: { type: integer, default: 0 }
```

### APIConfig 模型

```yaml
APIConfig:
  type: object
  properties:
    id: { type: string }
    name: { type: string }
    provider: { type: string, enum: ["volcengine", "openai", "azure", "google", "baidu", "alibaba", "custom"] }
    service_type: { type: string, enum: ["image_generation", "audio_generation", "translation", "video_synthesis"] }
    api_key: { type: string }
    api_secret: { type: string, nullable: true }
    endpoint: { type: string, nullable: true }
    region: { type: string, nullable: true }
    is_active: { type: boolean }
    is_default: { type: boolean, default: false }
    is_verified: { type: boolean, default: false }
    last_verified: { type: string, format: date-time, nullable: true }
    monthly_limit: { type: integer, nullable: true }
    daily_limit: { type: integer, nullable: true }
    rate_limit: { type: integer, nullable: true }
    current_usage: { type: integer, default: 0 }
    total_usage: { type: integer, default: 0 }
    cost_this_month: { type: number, default: 0.00 }
    total_cost: { type: number, default: 0.00 }
    last_used: { type: string, format: date-time, nullable: true }
    last_error: { type: string, nullable: true }
    error_count: { type: integer, default: 0 }
    success_count: { type: integer, default: 0 }
    config_params: { type: object, nullable: true }
    pricing_model: { type: object, nullable: true }
    created_at: { type: string, format: date-time }
    updated_at: { type: string, format: date-time }
    expires_at: { type: string, format: date-time, nullable: true }
```

### Timeline 模型

```yaml
Timeline:
  type: object
  properties:
    id: { type: string }
    chapter_id: { type: string }
    total_duration: { type: number }
    fps: { type: integer, default: 30 }
    resolution: { type: string, default: "1920x1080" }
    timeline_data: { type: object }
    audio_track_url: { type: string, nullable: true }
    audio_duration: { type: number, nullable: true }
    audio_sample_rate: { type: integer, nullable: true }
    subtitle_track_url: { type: string, nullable: true }
    subtitle_format: { type: string, default: "srt" }
    background_music_url: { type: string, nullable: true }
    background_music_volume: { type: number, default: 0.1 }
    processing_status: { type: string, default: "pending" }
    error_message: { type: string, nullable: true }
    created_at: { type: string, format: date-time }
    updated_at: { type: string, format: date-time }
```

## API 安全规范

### 认证机制

```yaml
# JWT Token 载荷
TokenPayload:
  type: object
  properties:
    user_id: { type: string }
    exp: { type: integer }
    iat: { type: integer }
    type: { type: string, enum: ["access", "refresh"] }

# 刷新Token
POST /api/v1/auth/refresh
requestBody:
  type: object
  properties:
    refresh_token: { type: string }
```

### 权限控制

```yaml
# 权限级别定义
Permission:
  type: object
  properties:
    resource: { type: string }
    action: { type: string, enum: ["read", "write", "delete"] }
    scope: { type: string, enum: ["own", "all"] }

# 权限检查中间件
Authorization:
  header: Authorization: Bearer {token}
  required_roles: []
  required_permissions: []
```

### 限流规则

```yaml
RateLimiting:
  global:
    requests_per_minute: 1000
    burst: 100

  per_user:
    upload: "5 files per minute"
    generation: "10 tasks per minute"
    api_calls: "100 requests per minute"

  per_ip:
    requests_per_minute: 200
    burst: 50
```

---

**合约版本**: 1.0.0
**最后更新**: 2025-11-06
**兼容性**: 向后兼容，增加字段不破坏现有客户端