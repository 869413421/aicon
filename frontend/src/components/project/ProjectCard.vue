<template>
  <div class="project-card" @click="$emit('view', project)">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="file-icon">
        <el-icon :size="32" :color="getFileTypeColor(project.file_type)">
          <component :is="getFileTypeIcon(project.file_type)" />
        </el-icon>
      </div>

      <div class="card-actions">
        <el-dropdown @command="handleCommand" trigger="click" @click.stop>
          <el-button type="text" size="small" :icon="More" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :command="`view:${project.id}`" :icon="View">
                查看详情
              </el-dropdown-item>
              <el-dropdown-item :command="`edit:${project.id}`" :icon="Edit">
                编辑项目
              </el-dropdown-item>
              <el-dropdown-item :command="`download:${project.id}`" :icon="Download">
                下载文件
              </el-dropdown-item>
              <el-dropdown-item :command="`duplicate:${project.id}`" :icon="CopyDocument">
                复制项目
              </el-dropdown-item>
              <el-dropdown-item
                :command="`archive:${project.id}`"
                :icon="FolderOpened"
                :disabled="project.status === 'archived'"
              >
                {{ project.status === 'archived' ? '已归档' : '归档' }}
              </el-dropdown-item>
              <el-dropdown-item
                :command="`delete:${project.id}`"
                :icon="Delete"
                divided
                danger
              >
                删除项目
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="card-content">
      <h3 class="project-title" :title="project.title">
        {{ project.title }}
      </h3>

      <p class="project-description" :title="project.description">
        {{ project.description || '暂无描述' }}
      </p>

      <!-- 文件信息 -->
      <div class="file-info">
        <div class="info-item">
          <el-text size="small" type="info">
            {{ getFileTypeText(project.file_type) }}
          </el-text>
          <el-text size="small" type="info">
            {{ formatFileSize(project.file_size) }}
          </el-text>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-info">
        <div class="stat-item">
          <el-text size="small">{{ formatNumber(project.word_count) }}</el-text>
          <el-text size="small" type="info">字数</el-text>
        </div>
        <div class="stat-item">
          <el-text size="small">{{ formatNumber(project.total_paragraphs) }}</el-text>
          <el-text size="small" type="info">段落</el-text>
        </div>
        <div class="stat-item" v-if="project.total_chapters > 0">
          <el-text size="small">{{ formatNumber(project.total_chapters) }}</el-text>
          <el-text size="small" type="info">章节</el-text>
        </div>
      </div>

      <!-- 状态标签 -->
      <div class="status-tags">
        <el-tag
          :type="getStatusType(project.status)"
          size="small"
          effect="plain"
        >
          {{ getStatusText(project.status) }}
        </el-tag>

        <el-tag
          :type="getFileStatusType(project.file_processing_status)"
          size="small"
          effect="plain"
        >
          {{ getFileStatusText(project.file_processing_status) }}
        </el-tag>

        <el-tag
          v-if="project.is_public"
          type="info"
          size="small"
          effect="plain"
        >
          公开
        </el-tag>
      </div>

      <!-- 处理进度条 -->
      <div v-if="project.file_processing_status === 'processing'" class="progress-section">
        <el-progress
          :percentage="project.processing_progress || 0"
          :show-text="false"
          :stroke-width="4"
        />
        <el-text size="small" type="info">
          处理进度: {{ Math.round(project.processing_progress || 0) }}%
        </el-text>
      </div>
    </div>

    <!-- 卡片底部 -->
    <div class="card-footer">
      <div class="time-info">
        <el-text size="small" type="info">
          创建于 {{ formatDateTime(project.created_at) }}
        </el-text>
        <el-text size="small" type="info">
          更新于 {{ formatDateTime(project.updated_at) }}
        </el-text>
      </div>

      <div class="action-buttons">
        <el-button
          type="primary"
          size="small"
          @click.stop="$emit('view', project)"
        >
          查看
        </el-button>
        <el-button
          size="small"
          @click.stop="$emit('edit', project)"
        >
          编辑
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  View,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
  Document,
  VideoPlay,
  Microphone,
  Picture
} from '@element-plus/icons-vue'

// Props定义
const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

// Emits定义
const emit = defineEmits([
  'view',
  'edit',
  'delete',
  'download',
  'duplicate',
  'archive'
])

// 计算属性
const getFileTypeIcon = (fileType) => {
  const iconMap = {
    'txt': Document,
    'md': Document,
    'docx': Document,
    'epub': Document,
    'video': VideoPlay,
    'audio': Microphone,
    'image': Picture
  }
  return iconMap[fileType] || Document
}

const getFileTypeColor = (fileType) => {
  const colorMap = {
    'txt': '#606266',
    'md': '#409EFF',
    'docx': '#67C23A',
    'epub': '#E6A23C',
    'video': '#F56C6C',
    'audio': '#909399',
    'image': '#909399'
  }
  return colorMap[fileType] || '#606266'
}

const getFileTypeText = (fileType) => {
  const textMap = {
    'txt': 'TXT',
    'md': 'Markdown',
    'docx': 'Word',
    'epub': 'EPUB',
    'video': '视频',
    'audio': '音频',
    'image': '图片'
  }
  return textMap[fileType] || '未知'
}

// 方法
const handleCommand = (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'view':
      emit('view', props.project)
      break
    case 'edit':
      emit('edit', props.project)
      break
    case 'download':
      emit('download', props.project)
      break
    case 'duplicate':
      emit('duplicate', props.project)
      break
    case 'archive':
      emit('archive', props.project)
      break
    case 'delete':
      emit('delete', props.project)
      break
  }
}

const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    archived: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    archived: '已归档'
  }
  return textMap[status] || status
}

const getFileStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    uploading: 'warning',
    uploaded: 'success',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getFileStatusText = (status) => {
  const textMap = {
    pending: '等待',
    uploading: '上传中',
    uploaded: '已上传',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  const now = new Date()
  const diffTime = now - date
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }
}
</script>

<style scoped>
.project-card {
  @apply bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden;
  height: 320px;
  display: flex;
  flex-direction: column;
}

.card-header {
  @apply flex items-center justify-between p-4 pb-2;
}

.file-icon {
  @apply flex items-center justify-center w-12 h-12 rounded-lg bg-gray-50;
}

.card-actions {
  @apply opacity-0 hover:opacity-100 transition-opacity duration-200;
}

.project-card:hover .card-actions {
  @apply opacity-100;
}

.card-content {
  @apply flex-1 px-4 pb-2;
}

.project-title {
  @apply text-base font-semibold text-gray-900 truncate mb-1;
  line-height: 1.4;
}

.project-description {
  @apply text-sm text-gray-600 line-clamp-2 mb-3;
  line-height: 1.5;
  height: 2.8em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.file-info {
  @apply mb-3;
}

.info-item {
  @apply flex items-center gap-2;
}

.stats-info {
  @apply flex items-center gap-4 mb-3;
}

.stat-item {
  @apply flex flex-col items-center;
}

.status-tags {
  @apply flex flex-wrap gap-1 mb-3;
}

.progress-section {
  @apply space-y-2;
}

.card-footer {
  @apply px-4 py-3 border-t border-gray-100 bg-gray-50;
}

.time-info {
  @apply flex justify-between text-xs text-gray-500 mb-3;
}

.action-buttons {
  @apply flex gap-2 justify-end;
}

.action-buttons .el-button {
  @apply flex-1;
}
</style>