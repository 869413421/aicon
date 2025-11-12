<template>
  <div class="project-detail">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 项目详情内容 -->
    <div v-else-if="project" class="detail-content">
      <!-- 头部操作栏 -->
      <div class="detail-header">
        <div class="header-left">
          <el-button :icon="ArrowLeft" @click="handleBack">
            返回
          </el-button>
          <div class="breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item @click="handleBack">项目列表</el-breadcrumb-item>
              <el-breadcrumb-item>{{ project.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>

        <div class="header-actions">
          <el-button-group>
            <el-button
              :icon="Edit"
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-button
              :icon="Download"
              @click="handleDownload"
            >
              下载
            </el-button>
            <el-dropdown @command="handleCommand">
              <el-button :icon="More">
                更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    :command="`duplicate:${project.id}`"
                    :icon="CopyDocument"
                  >
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
                    :command="`reprocess:${project.id}`"
                    :icon="Refresh"
                    :disabled="project.file_processing_status === 'processing'"
                  >
                    重新处理
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
          </el-button-group>
        </div>
      </div>

      <!-- 项目基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <h2 class="card-title">{{ project.title }}</h2>
            <div class="status-tags">
              <el-tag :type="getStatusType(project.status)" effect="plain">
                {{ getStatusText(project.status) }}
              </el-tag>
              <el-tag :type="getFileStatusType(project.file_processing_status)" effect="plain">
                {{ getFileStatusText(project.file_processing_status) }}
              </el-tag>
              <el-tag v-if="project.is_public" type="info" effect="plain">
                公开
              </el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="24">
          <!-- 左侧信息 -->
          <el-col :span="16">
            <div class="project-description">
              <h3>项目描述</h3>
              <p>{{ project.description || '暂无描述' }}</p>
            </div>

            <!-- 文件信息 -->
            <div class="file-info-section">
              <h3>文件信息</h3>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="原始文件名">
                  {{ project.original_filename || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型">
                  {{ getFileTypeText(project.file_type) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(project.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件格式">
                  {{ project.file_extension?.toUpperCase() || '-' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 内容统计 -->
            <div class="content-stats">
              <h3>内容统计</h3>
              <el-row :gutter="16">
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.word_count) }}</div>
                    <div class="stat-label">总字数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.total_paragraphs) }}</div>
                    <div class="stat-label">段落数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.total_sentences) }}</div>
                    <div class="stat-label">句子数</div>
                  </div>
                </el-col>
                <el-col :span="6" v-if="project.total_chapters > 0">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.total_chapters) }}</div>
                    <div class="stat-label">章节数</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-col>

          <!-- 右侧信息 -->
          <el-col :span="8">
            <!-- 处理进度 -->
            <div v-if="project.file_processing_status === 'processing'" class="progress-card">
              <h3>处理进度</h3>
              <el-progress
                type="circle"
                :percentage="project.processing_progress || 0"
                :width="120"
                :stroke-width="8"
              />
              <div class="progress-text">
                {{ Math.round(project.processing_progress || 0) }}% 完成
              </div>
            </div>

            <!-- 时间信息 -->
            <div class="time-info">
              <h3>时间信息</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="创建时间">
                  {{ formatDateTime(project.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ formatDateTime(project.updated_at) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="project.processed_at" label="处理完成时间">
                  {{ formatDateTime(project.processed_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 项目元数据 -->
            <div class="metadata-section">
              <h3>项目元数据</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="项目ID">
                  <el-text type="info" size="small">{{ project.id }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="存储对象键" v-if="project.minio_object_key">
                  <el-text type="info" size="small" class="object-key">
                    {{ project.minio_object_key }}
                  </el-text>
                </el-descriptions-item>
                <el-descriptions-item label="文件哈希" v-if="project.file_hash">
                  <el-text type="info" size="small">{{ project.file_hash }}</el-text>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <el-button type="primary" :icon="VideoPlay" @click="handleStartGeneration">
          开始视频生成
        </el-button>
        <el-button :icon="Document" @click="handleViewContent">
          查看文件内容
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="refreshing">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="handleRefresh">
            重新加载
          </el-button>
          <el-button @click="handleBack">
            返回列表
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
  Refresh,
  VideoPlay,
  Document
} from '@element-plus/icons-vue'

// Props定义
const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  project: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

// Emits定义
const emit = defineEmits([
  'back',
  'edit',
  'delete',
  'download',
  'duplicate',
  'archive',
  'reprocess',
  'refresh',
  'start-generation',
  'view-content'
])

// 响应式数据
const refreshing = ref(false)

// 方法
const handleBack = () => {
  emit('back')
}

const handleEdit = () => {
  emit('edit', props.project)
}

const handleDownload = () => {
  emit('download', props.project)
}

const handleCommand = async (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'duplicate':
      await handleDuplicate()
      break
    case 'archive':
      await handleArchive()
      break
    case 'reprocess':
      await handleReprocess()
      break
    case 'delete':
      await handleDelete()
      break
  }
}

const handleDuplicate = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要复制项目 "${props.project.title}" 吗？`,
      '确认复制',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    if (confirmed) {
      emit('duplicate', props.project)
      ElMessage.success('项目复制请求已发送')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleArchive = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要${props.project.status === 'archived' ? '取消归档' : '归档'}项目 "${props.project.title}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (confirmed) {
      emit('archive', props.project)
      ElMessage.success(props.project.status === 'archived' ? '取消归档成功' : '归档成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleReprocess = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要重新处理项目 "${props.project.title}" 的文件吗？`,
      '确认重新处理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (confirmed) {
      emit('reprocess', props.project)
      ElMessage.success('重新处理请求已发送')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleDelete = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要删除项目 "${props.project.title}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )

    if (confirmed) {
      emit('delete', props.project)
      ElMessage.success('项目删除成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleStartGeneration = () => {
  if (props.project.file_processing_status !== 'completed') {
    ElMessage.warning('文件处理完成后才能开始视频生成')
    return
  }
  emit('start-generation', props.project)
}

const handleViewContent = () => {
  emit('view-content', props.project)
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh', props.projectId)
  } finally {
    setTimeout(() => {
      refreshing.value = false
    }, 1000)
  }
}

// 工具方法
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

const getFileTypeText = (fileType) => {
  const textMap = {
    txt: 'TXT文档',
    md: 'Markdown文档',
    docx: 'Word文档',
    epub: 'EPUB电子书'
  }
  return textMap[fileType] || '未知文件类型'
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
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.project-detail {
  @apply min-h-full;
}

.loading-container {
  @apply p-6;
}

.detail-content {
  @apply space-y-6;
}

.detail-header {
  @apply flex items-center justify-between mb-6;
}

.header-left {
  @apply flex items-center gap-4;
}

.breadcrumb {
  @apply hidden md:block;
}

.header-actions {
  @apply flex gap-2;
}

.card-header {
  @apply flex items-center justify-between;
}

.card-title {
  @apply text-xl font-semibold text-gray-900 m-0;
}

.status-tags {
  @apply flex gap-2;
}

.project-description,
.file-info-section,
.content-stats {
  @apply mb-6;
}

.project-description h3,
.file-info-section h3,
.content-stats h3 {
  @apply text-base font-semibold text-gray-900 mb-3;
}

.project-description p {
  @apply text-gray-600 leading-relaxed;
}

.stat-item {
  @apply text-center p-4 bg-gray-50 rounded-lg;
}

.stat-value {
  @apply text-2xl font-bold text-blue-600 mb-1;
}

.stat-label {
  @apply text-sm text-gray-500;
}

.progress-card {
  @apply mb-6 p-4 bg-gray-50 rounded-lg text-center;
}

.progress-card h3 {
  @apply text-base font-semibold text-gray-900 mb-4;
}

.progress-text {
  @apply mt-4 text-sm text-gray-600;
}

.time-info,
.metadata-section {
  @apply mb-6;
}

.time-info h3,
.metadata-section h3 {
  @apply text-base font-semibold text-gray-900 mb-3;
}

.object-key {
  @apply break-all;
  word-break: break-all;
}

.action-buttons {
  @apply flex gap-4 justify-center;
}

.error-state {
  @apply flex items-center justify-center min-h-96;
}

@media (max-width: 768px) {
  .detail-header {
    @apply flex-col items-start gap-4;
  }

  .header-left {
    @apply w-full;
  }

  .header-actions {
    @apply w-full justify-end;
  }

  .action-buttons {
    @apply flex-col;
  }
}
</style>