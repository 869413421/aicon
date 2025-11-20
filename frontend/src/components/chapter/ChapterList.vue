<template>
  <div class="chapter-list">
    <!-- 头部操作栏 -->
    <div class="chapter-header">
      <div class="header-left">
        <h3 class="section-title">
          <el-icon class="title-icon"><Document /></el-icon>
          章节管理
        </h3>
        <div class="chapter-count">
          共 {{ pagination.total }} 个章节
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="handleCreateChapter">
          新建章节
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索章节标题或内容"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="6">
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="handleFilter">
            <el-option label="全部状态" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="sortBy" placeholder="排序方式" @change="handleSort">
            <el-option label="章节序号" value="chapter_number" />
            <el-option label="创建时间" value="created_at" />
            <el-option label="更新时间" value="updated_at" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button :icon="Refresh" @click="handleRefresh" :loading="refreshing">
            刷新
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 章节列表 -->
    <div class="chapter-content">
      <el-empty v-if="!loading && chapters.length === 0" description="暂无章节数据">
        <el-button type="primary" @click="handleCreateChapter">创建第一个章节</el-button>
      </el-empty>

      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else class="chapter-cards">
        <el-card
          v-for="chapter in chapters"
          :key="chapter.id"
          class="chapter-card"
          :class="{ 'confirmed': chapter.is_confirmed }"
        >
          <template #header>
            <div class="chapter-card-header">
              <div class="chapter-info">
                <span class="chapter-number">第 {{ chapter.chapter_number }} 章</span>
                <h4 class="chapter-title">{{ chapter.title }}</h4>
              </div>
              <div class="chapter-actions">
                <el-tag v-if="chapter.is_confirmed" type="success" size="small">
                  已确认
                </el-tag>
                <el-tag :type="getStatusType(chapter.status)" size="small">
                  {{ getStatusText(chapter.status) }}
                </el-tag>
              </div>
            </div>
          </template>

          <div class="chapter-stats">
            <el-row :gutter="12">
              <el-col :span="6">
                <div class="stat-item">
                  <div class="stat-value">{{ formatNumber(chapter.word_count) }}</div>
                  <div class="stat-label">字数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item">
                  <div class="stat-value">{{ formatNumber(chapter.paragraph_count) }}</div>
                  <div class="stat-label">段落</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item">
                  <div class="stat-value">{{ formatNumber(chapter.sentence_count) }}</div>
                  <div class="stat-label">句子</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-item">
                  <div class="stat-value">{{ formatDateTime(chapter.created_at) }}</div>
                  <div class="stat-label">创建时间</div>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="chapter-content-preview">
            <p>{{ truncateContent(chapter.content, 100) }}</p>
          </div>

          <div class="chapter-card-footer">
            <div class="chapter-operations">
              <el-button size="small" @click="handleViewChapter(chapter)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" @click="handleManageParagraphs(chapter)">
                <el-icon><List /></el-icon>
                段落
              </el-button>
              <el-button
                v-if="!chapter.is_confirmed && chapter.status === 'completed'"
                size="small"
                type="success"
                @click="handleConfirmChapter(chapter)"
              >
                <el-icon><Check /></el-icon>
                确认
              </el-button>
              <el-button
                v-if="!chapter.is_confirmed"
                size="small"
                type="primary"
                @click="handleEditChapter(chapter)"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                v-if="!chapter.is_confirmed"
                size="small"
                type="danger"
                @click="handleDeleteChapter(chapter)"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="chapters.length > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑章节对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <ChapterForm
        v-if="dialogVisible"
        :chapter="currentChapter"
        :project-id="projectId"
        @submit="handleChapterSubmit"
        @cancel="handleDialogClose"
      />
    </el-dialog>

    <!-- 章节详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="章节详情"
      width="800px"
    >
      <ChapterDetail
        v-if="detailVisible"
        :chapter="currentChapter"
        @edit="handleEditFromDetail"
        @close="detailVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Plus,
  Search,
  Refresh,
  View,
  Edit,
  Delete,
  Check,
  List
} from '@element-plus/icons-vue'
import chaptersService from '@/services/chapters'
import ChapterForm from './ChapterForm.vue'
import ChapterDetail from './ChapterDetail.vue'

// Props
const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['close'])

const router = useRouter()

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const chapters = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('chapter_number')

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框状态
const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogTitle = ref('')
const currentChapter = ref(null)
const editingChapterId = ref(null)

// 状态映射
const statusMap = {
  pending: { type: 'info', text: '待处理' },
  confirmed: { type: 'success', text: '已确认' },
  processing: { type: 'warning', text: '处理中' },
  completed: { type: 'success', text: '已完成' },
  failed: { type: 'danger', text: '失败' }
}

// 方法
const getStatusType = (status) => {
  return statusMap[status]?.type || 'info'
}

const getStatusText = (status) => {
  return statusMap[status]?.text || status
}

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

const truncateContent = (content, length) => {
  return content && content.length > length
    ? content.substring(0, length) + '...'
    : content
}

const loadChapters = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: searchQuery.value,
      status: statusFilter.value,
      sort_by: sortBy.value
    }

    const response = await chaptersService.getChapters(props.projectId, params)
    chapters.value = response.chapters
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载章节数据失败')
    console.error('加载章节失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadChapters()
}

const handleFilter = () => {
  pagination.page = 1
  loadChapters()
}

const handleSort = () => {
  pagination.page = 1
  loadChapters()
}

const handleRefresh = () => {
  refreshing.value = true
  loadChapters().finally(() => {
    setTimeout(() => {
      refreshing.value = false
    }, 1000)
  })
}

const handleSizeChange = (newSize) => {
  pagination.size = newSize
  pagination.page = 1
  loadChapters()
}

const handleCurrentChange = (newPage) => {
  pagination.page = newPage
  loadChapters()
}

const handleCreateChapter = () => {
  dialogTitle.value = '新建章节'
  currentChapter.value = null
  editingChapterId.value = null
  dialogVisible.value = true
}

const handleViewChapter = (chapter) => {
  currentChapter.value = chapter
  detailVisible.value = true
}

const handleEditChapter = (chapter) => {
  dialogTitle.value = '编辑章节'
  currentChapter.value = { ...chapter }
  editingChapterId.value = chapter.id
  dialogVisible.value = true
}

const handleEditFromDetail = (chapter) => {
  detailVisible.value = false
  handleEditChapter(chapter)
}

const handleDeleteChapter = async (chapter) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除章节"${chapter.title}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await chaptersService.deleteChapter(chapter.id)
    ElMessage.success('章节删除成功')
    loadChapters()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除章节失败')
      console.error('删除章节失败:', error)
    }
  }
}

const handleConfirmChapter = async (chapter) => {
  try {
    await chaptersService.confirmChapter(chapter.id)
    ElMessage.success('章节确认成功')
    loadChapters()
  } catch (error) {
    ElMessage.error('确认章节失败')
    console.error('确认章节失败:', error)
  }
}

const handleManageParagraphs = (chapter) => {
  router.push({
    name: 'ParagraphManagement',
    params: {
      projectId: props.projectId,
      chapterId: chapter.id
    }
  })
}

const handleChapterSubmit = async (chapterData) => {
  try {
    if (editingChapterId.value) {
      // 更新章节
      await chaptersService.updateChapter(editingChapterId.value, chapterData)
      ElMessage.success('章节更新成功')
    } else {
      // 创建章节
      await chaptersService.createChapter(props.projectId, chapterData)
      ElMessage.success('章节创建成功')
    }

    dialogVisible.value = false
    loadChapters()
  } catch (error) {
    ElMessage.error(editingChapterId.value ? '更新章节失败' : '创建章节失败')
    console.error('章节操作失败:', error)
  }
}

const handleDialogClose = () => {
  dialogVisible.value = false
  currentChapter.value = null
  editingChapterId.value = null
}

// 生命周期
onMounted(() => {
  loadChapters()
})
</script>

<style scoped>
.chapter-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  font-size: var(--text-xl);
  color: var(--primary-color);
}

.chapter-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.search-bar {
  padding: var(--space-lg);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.chapter-content {
  flex: 1;
}

.loading-container {
  padding: var(--space-xl);
}

.chapter-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--space-lg);
}

.chapter-card {
  transition: all var(--transition-fast);
}

.chapter-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.chapter-card.confirmed {
  border-color: var(--success-color);
}

.chapter-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
}

.chapter-info {
  flex: 1;
}

.chapter-number {
  font-size: var(--text-sm);
  color: var(--primary-color);
  font-weight: 600;
  display: block;
  margin-bottom: var(--space-xs);
}

.chapter-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.4;
}

.chapter-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  align-items: flex-end;
}

.chapter-stats {
  margin-bottom: var(--space-md);
}

.stat-item {
  text-align: center;
  padding: var(--space-sm);
}

.stat-value {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
}

.chapter-content-preview {
  margin-bottom: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.chapter-content-preview p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.chapter-card-footer {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--border-primary);
  padding-top: var(--space-md);
}

.chapter-operations {
  display: flex;
  gap: var(--space-sm);
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: var(--space-lg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chapter-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .chapter-cards {
    grid-template-columns: 1fr;
  }

  .chapter-card-header {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .chapter-actions {
    flex-direction: row;
    align-items: flex-start;
  }

  .search-bar :deep(.el-row) {
    flex-direction: column;
  }

  .search-bar :deep(.el-col) {
    width: 100%;
    margin-bottom: var(--space-sm);
  }
}
</style>