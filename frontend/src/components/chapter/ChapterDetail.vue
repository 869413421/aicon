<template>
  <div class="chapter-detail">
    <!-- 章节基本信息 -->
    <div class="chapter-header">
      <div class="chapter-info">
        <h2 class="chapter-title">
          第 {{ chapter.chapter_number }} 章 - {{ chapter.title }}
        </h2>
        <div class="chapter-meta">
          <el-tag v-if="chapter.is_confirmed" type="success" size="large">
            <el-icon class="tag-icon"><Check /></el-icon>
            已确认
          </el-tag>
          <el-tag :type="getStatusType(chapter.status)" size="large">
            {{ getStatusText(chapter.status) }}
          </el-tag>
        </div>
      </div>
      <div class="chapter-operations">
        <el-button
          v-if="!chapter.is_confirmed && chapter.status === 'completed'"
          type="success"
          @click="handleConfirmChapter"
        >
          <el-icon><Check /></el-icon>
          确认章节
        </el-button>
        <el-button type="primary" plain @click="handleManageParagraphs">
          <el-icon><List /></el-icon>
          段落
        </el-button>
        <el-button @click="$emit('close')">
          关闭
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <h3 class="section-title">统计信息</h3>
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(chapter.word_count) }}</div>
              <div class="stat-label">总字数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(chapter.paragraph_count) }}</div>
              <div class="stat-label">段落数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><ChatLineSquare /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(chapter.sentence_count) }}</div>
              <div class="stat-label">句子数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatDuration(chapter.video_duration) }}</div>
              <div class="stat-label">视频时长</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 章节内容 -->
    <div class="content-section">
      <h3 class="section-title">章节内容</h3>
      <div class="content-card">
        <div class="content-text">
          {{ chapter.content }}
        </div>
        <div v-if="chapter.edited_content" class="edited-content">
          <h4>编辑内容</h4>
          <div class="edited-text">
            {{ chapter.edited_content }}
          </div>
          <div v-if="chapter.editing_notes" class="editing-notes">
            <h5>编辑备注</h5>
            <p>{{ chapter.editing_notes }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态详情 -->
    <div class="status-section">
      <h3 class="section-title">状态详情</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="处理状态">
          <el-tag :type="getStatusType(chapter.status)">
            {{ getStatusText(chapter.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="确认状态">
          <el-tag :type="chapter.is_confirmed ? 'success' : 'info'">
            {{ chapter.is_confirmed ? '已确认' : '未确认' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(chapter.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(chapter.updated_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="chapter.confirmed_at" label="确认时间">
          {{ formatDateTime(chapter.confirmed_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="chapter.video_url" label="视频地址">
          <el-link :href="chapter.video_url" target="_blank" type="primary">
            查看视频
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item v-if="chapter.video_duration" label="视频时长">
          {{ formatDuration(chapter.video_duration) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 确认章节对话框 -->
    <el-dialog
      v-model="confirmDialogVisible"
      title="确认章节"
      width="400px"
    >
      <p>确定要确认章节"{{ chapter.title }}"吗？</p>
      <p class="confirm-note">
        确认后的章节将不能编辑或删除。
      </p>
      <template #footer>
        <el-button @click="confirmDialogVisible = false">取消</el-button>
        <el-button type="success" @click="handleConfirmChapter" :loading="confirming">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Check,
  Document,
  Collection,
  ChatLineSquare,
  Timer,
  List
} from '@element-plus/icons-vue'

const router = useRouter()

const props = defineProps({
  chapter: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'refresh'])

const confirmDialogVisible = ref(false)
const confirming = ref(false)

// 方法
const formatNumber = (num) => {
  return num ? num.toLocaleString() : 0
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

const getStatusType = (status) => {
  const statusMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const handleManageParagraphs = () => {
  router.push({
    name: 'ParagraphManagement',
    params: {
      projectId: props.chapter.project_id,
      chapterId: props.chapter.id
    }
  })
}

const handleConfirmChapter = async () => {
  confirmDialogVisible.value = false
  confirming.value = true
  
  try {
    // TODO: 调用确认章节的API
    ElMessage.success('章节确认成功')
    emit('refresh')
  } catch (error) {
    console.error('确认章节失败:', error)
    ElMessage.error('确认章节失败')
  } finally {
    confirming.value = false
  }
}
</script>

<style scoped>
.chapter-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg);
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-lg);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02), rgba(139, 92, 246, 0.02));
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.chapter-info {
  flex: 1;
}

.chapter-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
  line-height: 1.4;
}

.chapter-meta {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

.tag-icon {
  margin-right: var(--space-xs);
}

.chapter-operations {
  display: flex;
  gap: var(--space-sm);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.section-title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, var(--primary-color), var(--primary-hover));
  border-radius: var(--radius-sm);
}

.stats-section {
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-fast);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border-radius: var(--radius-lg);
  color: white;
  font-size: var(--text-xl);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.content-section {
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.content-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.content-text {
  padding: var(--space-lg);
  line-height: 1.8;
  color: var(--text-primary);
  font-size: var(--text-base);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.edited-content {
  border-top: 1px solid var(--border-primary);
  padding: var(--space-lg);
  background: rgba(103, 194, 58, 0.05);
}

.edited-content h4 {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--success-color);
  margin: 0 0 var(--space-md) 0;
}

.edited-text {
  line-height: 1.8;
  color: var(--text-primary);
  font-size: var(--text-base);
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-bottom: var(--space-md);
}

.editing-notes {
  padding: var(--space-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.editing-notes h5 {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-xs) 0;
}

.editing-notes p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.5;
}

.status-section {
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

:deep(.el-descriptions) {
  --el-descriptions-table-border: 1px solid var(--border-primary);
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-secondary);
  width: 120px;
}

:deep(.el-descriptions__content) {
  color: var(--text-secondary);
}

.confirm-note {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin: var(--space-md) 0;
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--warning-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chapter-header {
    flex-direction: column;
    gap: var(--space-md);
  }

  .chapter-operations {
    width: 100%;
    justify-content: flex-start;
  }

  .stats-section :deep(.el-col) {
    margin-bottom: var(--space-md);
  }

  .stat-card {
    padding: var(--space-md);
  }

  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: var(--text-lg);
  }

  .stat-value {
    font-size: var(--text-base);
  }

  :deep(.el-descriptions__label) {
    width: 100px;
  }
}
</style>