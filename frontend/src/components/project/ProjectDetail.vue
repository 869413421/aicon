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
        <el-button :icon="ArrowLeft" @click="handleBack">
          返回
        </el-button>
        <h2 class="page-title">{{ project.title }}</h2>
      </div>

      <!-- 项目基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <h2 class="card-title">{{ project.title }}</h2>
            <div class="status-tags">
              <el-tag :type="projectsStore.getStatusType(project.status)" effect="plain">
                {{ projectsStore.getStatusText(project.status) }}
              </el-tag>
              <el-tag v-if="project.is_public" type="info" effect="plain">
                公开
              </el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="24">
          <!-- 左侧信息 -->
          <el-col :span="12">
            <!-- 文件信息 -->
            <div class="file-info-section">
              <h3>文件信息</h3>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="文件名">
                  {{ project.file_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型">
                  {{ project.file_type?.toUpperCase() || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ projectsStore.formatFileSize(project.file_size) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 内容统计 -->
            <div class="content-stats">
              <h3>内容统计</h3>
              <el-row :gutter="16">
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ projectsStore.formatNumber(project.word_count) }}</div>
                    <div class="stat-label">总字数</div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ projectsStore.formatNumber(project.paragraph_count) }}</div>
                    <div class="stat-label">段落数</div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ projectsStore.formatNumber(project.sentence_count) }}</div>
                    <div class="stat-label">句子数</div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ projectsStore.formatNumber(project.chapter_count) }}</div>
                    <div class="stat-label">章节数</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-col>

          <!-- 右侧信息 -->
          <el-col :span="12">
            <!-- 处理进度 -->
            <div v-if="project.status === 'parsing' || project.status === 'generating'" class="progress-card">
              <h3>处理进度</h3>
              <el-progress
                type="circle"
                :percentage="project.processing_progress || 0"
                :width="80"
                :stroke-width="6"
              />
              <div class="progress-text">
                {{ Math.round(project.processing_progress || 0) }}% 完成
              </div>
            </div>

            <!-- 时间和状态信息 -->
            <div class="info-section">
              <h3>项目信息</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="状态">
                  <el-tag :type="projectsStore.getStatusType(project.status)" effect="plain">
                    {{ projectsStore.getStatusText(project.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ projectsStore.formatDateTime(project.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ projectsStore.formatDateTime(project.updated_at) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="project.processed_at" label="处理完成时间">
                  {{ projectsStore.formatDateTime(project.processed_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <!-- 主要操作 -->
        <el-button
          v-if="projectsStore.isEditable(project)"
          type="primary"
          :icon="Edit"
          @click="handleEdit"
        >
          编辑项目
        </el-button>
        <el-button
          v-if="['completed', 'parsed'].includes(project.status)"
          type="success"
          :icon="VideoPlay"
          @click="handleStartGeneration"
        >
          开始视频生成
        </el-button>

  
        <!-- 危险操作 -->
        <el-button
          v-if="projectsStore.isArchivable(project)"
          type="warning"
          :icon="Lock"
          @click="handleArchive"
        >
          归档项目
        </el-button>
        <el-button
          v-if="project.status === 'failed'"
          type="warning"
          :icon="RefreshRight"
          @click="handleReprocess"
        >
          重试
        </el-button>
        <el-button
          v-if="project.status === 'completed'"
          type="info"
          :icon="Refresh"
          @click="handleReprocess"
        >
          重新处理
        </el-button>

        <!-- 刷新 -->
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  VideoPlay,
  Edit,
  Lock,
  Refresh,
  RefreshRight
} from '@element-plus/icons-vue'
import { useProjectsStore } from '@/stores/projects'

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

// Store实例
const projectsStore = useProjectsStore()

// Emits定义
const emit = defineEmits([
  'back',
  'refresh',
  'start-generation',
  'edit',
  'archive',
  'reprocess'
])

// 响应式数据
const refreshing = ref(false)

// 状态轮询
const pollingInterval = ref(null)

// 方法
const handleBack = () => {
  emit('back')
}


const handleStartGeneration = () => {
  if (!['completed', 'parsed'].includes(props.project.status)) {
    ElMessage.warning('文件处理完成后才能开始视频生成')
    return
  }
  emit('start-generation', props.project)
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

const handleEdit = () => {
  emit('edit', props.project)
}

const handleArchive = async () => {
  emit('archive', props.project)
}

const handleReprocess = () => {
  emit('reprocess', props.project)

  // 重试后重新开始状态轮询
  setTimeout(() => {
    startStatusPolling()
  }, 1000) // 延迟1秒后开始轮询，确保状态已更新
}

// 状态轮询相关方法
const startStatusPolling = () => {
  // 清理已有的轮询
  stopStatusPolling()

  // 只有在处理中的状态才进行轮询
  if (!props.project || !['uploaded', 'parsing', 'generating'].includes(props.project.status)) {
    return
  }

  // 立即查询一次状态
  pollProjectStatus()

  // 设置定时轮询
  pollingInterval.value = setInterval(() => {
    pollProjectStatus()
  }, 3000) // 每3秒轮询一次
}

const stopStatusPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

const pollProjectStatus = async () => {
  try {
    const statusResponse = await projectsStore.fetchProjectStatus(props.projectId)

    // 如果处理完成或失败，停止轮询
    const finalStatuses = ['parsed', 'completed', 'failed', 'archived']
    if (finalStatuses.includes(statusResponse.project.status)) {
      stopStatusPolling()
      // 发出刷新事件，让父组件更新项目数据
      emit('refresh', props.projectId)
    }

  } catch (error) {
    console.error('轮询项目状态失败:', error)
    // 轮询失败不显示错误，避免打扰用户
  }
}

// 生命周期和监听器
onMounted(() => {
  // 组件挂载时开始状态轮询
  startStatusPolling()
})

onUnmounted(() => {
  // 组件卸载时清理轮询
  stopStatusPolling()
})

// 监听项目变化，重新开始轮询
watch(() => props.project, (newProject) => {
  if (newProject) {
    startStatusPolling()
  }
}, { immediate: true })

// 监听projectId变化
watch(() => props.projectId, () => {
  startStatusPolling()
})

// 使用store中的工具方法，避免重复代码
</script>

<style scoped>
.project-detail {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg);
}

.loading-container {
  padding: var(--space-xl);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  flex: 1;
}

/* 卡片样式 */
:deep(.el-card) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

:deep(.el-card__header) {
  padding: var(--space-xl);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02), rgba(139, 92, 246, 0.02));
  border-bottom: 1px solid var(--border-primary);
}

:deep(.el-card__body) {
  padding: var(--space-xl);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.status-tags {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

/* 内容区块样式 */
.file-info-section,
.content-stats,
.info-section {
  margin-bottom: var(--space-xl);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.file-info-section h3,
.content-stats h3,
.info-section h3 {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-lg) 0;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.file-info-section h3::before,
.content-stats h3::before,
.info-section h3::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, var(--primary-color), var(--primary-hover));
  border-radius: var(--radius-sm);
}

/* 统计信息样式 */
.stat-item {
  text-align: center;
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  margin-bottom: var(--space-md);
  transition: all var(--transition-fast);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-color);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: var(--space-sm);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 进度卡片样式 */
.progress-card {
  padding: var(--space-xl);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.2);
  text-align: center;
  margin-bottom: var(--space-lg);
  position: relative;
}

.progress-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
}

.progress-card h3 {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
}

.progress-text {
  margin-top: var(--space-sm);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

/* 描述列表样式 */
:deep(.el-descriptions) {
  --el-descriptions-table-border: 1px solid var(--border-primary);
  --el-descriptions-item-bordered-background: var(--bg-secondary);
}

:deep(.el-descriptions__label) {
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-secondary);
}

:deep(.el-descriptions__content) {
  color: var(--text-secondary);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  justify-content: center;
  align-items: center;
  padding: var(--space-xl);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  margin-top: var(--space-lg);
}

.action-buttons .el-button {
  border-radius: var(--radius-lg);
  font-weight: 600;
  padding: var(--space-md) var(--space-lg);
  min-width: 120px;
  transition: all var(--transition-base);
}

.action-buttons .el-button--primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  box-shadow: var(--shadow-md);
}

.action-buttons .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.action-buttons .el-button--default {
  border-color: var(--border-primary);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.action-buttons .el-button--default:hover {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
  transform: translateY(-1px);
}

/* 错误状态样式 */
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: var(--space-xl);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-detail {
    padding: var(--space-md);
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
    padding: var(--space-md);
  }

  :deep(.el-card__header) {
    padding: var(--space-lg);
  }

  :deep(.el-card__body) {
    padding: var(--space-lg);
  }

  .file-info-section,
  .content-stats,
  .info-section {
    padding: var(--space-md);
    margin-bottom: var(--space-lg);
  }

  .stat-item {
    padding: var(--space-md);
  }

  .stat-value {
    font-size: var(--text-lg);
  }

  .progress-card {
    padding: var(--space-lg);
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
    padding: var(--space-lg);
  }

  .action-buttons .el-button {
    width: 100%;
    min-width: auto;
  }
}
</style>