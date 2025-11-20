<template>
  <div class="paragraph-management">
    <!-- 头部导航和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ name: 'Projects' }">项目列表</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ name: 'ProjectDetail', params: { projectId } }">项目详情</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ name: 'ChapterManagement', params: { projectId } }">章节管理</el-breadcrumb-item>
          <el-breadcrumb-item>段落管理</el-breadcrumb-item>
        </el-breadcrumb>
        <h2 class="page-title">
          <span v-if="chapter">第 {{ chapter.chapter_number }} 章 - {{ chapter.title }}</span>
          <span v-else>加载中...</span>
        </h2>
      </div>
      <div class="header-right">
        <el-button @click="handleBack">返回章节</el-button>
        <el-button type="success" @click="openCreateDialog">
          <el-icon class="el-icon--left"><Plus /></el-icon>
          新建段落
        </el-button>
        <el-button type="primary" @click="handleBatchSave" :loading="saving" :disabled="!hasChanges">
          保存修改
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content" v-loading="loading">
      <!-- 侧边栏：统计和筛选 -->
      <div class="sidebar">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>统计信息</span>
            </div>
          </template>
          <div class="stats-list">
            <div class="stat-item">
              <span class="label">总段落数</span>
              <span class="value">{{ paragraphs.length }}</span>
            </div>
            <div class="stat-item">
              <span class="label">未修改</span>
              <span class="value success">{{ countByAction('keep') }}</span>
            </div>
            <div class="stat-item">
              <span class="label">已修改</span>
              <span class="value warning">{{ countByAction('edit') }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="filter-card">
          <template #header>
            <div class="card-header">
              <span>筛选显示</span>
            </div>
          </template>
          <el-radio-group v-model="filterStatus" class="filter-group">
            <el-radio label="all">全部显示</el-radio>
            <el-radio label="modified">仅显示已修改</el-radio>
          </el-radio-group>
        </el-card>
      </div>

      <!-- 列表区域 -->
      <div class="list-container">
        <el-empty v-if="!loading && filteredParagraphs.length === 0" description="暂无符合条件的段落" />
        
        <div v-else class="paragraph-list">
          <ParagraphItem
            v-for="(paragraph, index) in filteredParagraphs"
            :key="paragraph.id"
            :paragraph="paragraph"
            :index="getOriginalIndex(paragraph)"
            @update:action="updateAction"
            @update:content="updateContent"
            @update:ignore-reason="updateIgnoreReason"
          />
        </div>
      </div>
    </div>

    <!-- 新建段落对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建段落"
      width="500px"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="段落内容">
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="6"
            placeholder="请输入段落内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateParagraph" :loading="creating">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import chaptersService from '@/services/chapters'
import paragraphsService from '@/services/paragraphs'
import ParagraphItem from '@/components/paragraph/ParagraphItem.vue'

const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  chapterId: {
    type: String,
    required: true
  }
})

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const chapter = ref(null)
const paragraphs = ref([])
const originalParagraphs = ref([]) // 用于比对修改
const filterStatus = ref('all')

// 新建段落相关
const createDialogVisible = ref(false)
const creating = ref(false)
const createForm = reactive({
  content: ''
})

const openCreateDialog = () => {
  createForm.content = ''
  createDialogVisible.value = true
}

const handleCreateParagraph = async () => {
  if (!createForm.content.trim()) {
    ElMessage.warning('请输入段落内容')
    return
  }

  creating.value = true
  try {
    await paragraphsService.createParagraph(props.chapterId, {
      content: createForm.content
    })
    ElMessage.success('新建段落成功')
    createDialogVisible.value = false
    await fetchData()
  } catch (error) {
    console.error('新建段落失败:', error)
    ElMessage.error('新建段落失败')
  } finally {
    creating.value = false
  }
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // 并行获取章节信息和段落列表
    const [chapterRes, paragraphsRes] = await Promise.all([
      chaptersService.getChapter(props.chapterId),
      paragraphsService.getParagraphs(props.chapterId)
    ])
    
    chapter.value = chapterRes
    
    // 初始化段落数据
    paragraphs.value = paragraphsRes.paragraphs.map(p => ({
      ...p,
      edited_content: p.edited_content || p.content,
      action: p.action || 'keep', // 默认为保留
      ignore_reason: p.ignore_reason || ''
    }))
    
    // 深拷贝一份作为原始数据
    originalParagraphs.value = JSON.parse(JSON.stringify(paragraphs.value))
    
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 计算属性
const filteredParagraphs = computed(() => {
  if (filterStatus.value === 'all') return paragraphs.value
  
  return paragraphs.value.filter(p => {
    if (filterStatus.value === 'modified') return isModified(p)
    return true
  })
})

const hasChanges = computed(() => {
  return paragraphs.value.some(p => isModified(p))
})

// 辅助方法
const getOriginalIndex = (paragraph) => {
  return paragraphs.value.findIndex(p => p.id === paragraph.id) + 1
}

const countByAction = (action) => {
  return paragraphs.value.filter(p => p.action === action).length
}

const isModified = (paragraph) => {
  const original = originalParagraphs.value.find(p => p.id === paragraph.id)
  if (!original) return false
  
  return (
    paragraph.action !== original.action ||
    paragraph.edited_content !== original.edited_content ||
    paragraph.ignore_reason !== original.ignore_reason
  )
}

// 事件处理
const updateAction = (id, action) => {
  const p = paragraphs.value.find(item => item.id === id)
  if (p) p.action = action
}

const updateContent = (id, content) => {
  const p = paragraphs.value.find(item => item.id === id)
  if (p) p.edited_content = content
}

const updateIgnoreReason = (id, reason) => {
  const p = paragraphs.value.find(item => item.id === id)
  if (p) p.ignore_reason = reason
}

const handleBack = () => {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      '有未保存的修改，确定要离开吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      router.push({ name: 'ChapterManagement', params: { projectId: props.projectId } })
    }).catch(() => {})
  } else {
    router.push({ name: 'ChapterManagement', params: { projectId: props.projectId } })
  }
}

const handleBatchSave = async () => {
  const modifiedParagraphs = paragraphs.value.filter(isModified)
  
  if (modifiedParagraphs.length === 0) return

  saving.value = true
  try {
    await paragraphsService.batchUpdateParagraphs(props.chapterId, modifiedParagraphs)
    ElMessage.success(`成功保存 ${modifiedParagraphs.length} 个段落的修改`)
    // 重新获取数据以更新状态
    await fetchData()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存修改失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.paragraph-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  padding: var(--space-lg);
  background: var(--bg-base);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.main-content {
  flex: 1;
  display: flex;
  gap: var(--space-lg);
  overflow: hidden;
}

.sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  flex-shrink: 0;
}

.stats-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-xs) 0;
}

.stat-item .label {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.stat-item .value {
  font-weight: 600;
  font-size: var(--text-base);
}

.value.success { color: var(--success-color); }
.value.warning { color: var(--warning-color); }
.value.danger { color: var(--danger-color); }
.value.info { color: var(--info-color); }

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.list-container {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--space-sm);
}

.paragraph-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
    overflow-y: auto;
  }
  
  .sidebar {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .sidebar .el-card {
    flex: 1;
    min-width: 200px;
  }
  
  .list-container {
    overflow: visible;
  }
}
</style>
