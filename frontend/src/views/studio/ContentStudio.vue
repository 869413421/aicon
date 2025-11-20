<template>
  <div class="content-studio">
    <!-- 顶部工具栏 -->
    <div class="studio-header">
      <div class="header-left">
        <el-button @click="handleBack" :icon="ArrowLeft">返回项目</el-button>
        <el-divider direction="vertical" />
        <span class="project-title">{{ projectTitle }}</span>
      </div>
      <div class="header-right">
        <el-button 
          type="primary" 
          :loading="saving"
          :disabled="!hasChanges"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          保存修改
        </el-button>
      </div>
    </div>

    <!-- 统计信息面板 -->
    <div class="studio-stats">
      <div class="stat-item">
        <span class="stat-label">章节</span>
        <span class="stat-value">{{ totalChapters }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">段落</span>
        <span class="stat-value">{{ totalParagraphs }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总字数</span>
        <span class="stat-value">{{ totalWords }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已修改</span>
        <span class="stat-value">{{ hasChanges ? modifiedParagraphs.size : 0 }}</span>
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="studio-body">
      <!-- 左侧：章节导航 -->
      <ChapterNav
        :chapters="chapters"
        :selected-id="selectedChapterId"
        :loading="chaptersLoading"
        :has-more="hasMoreChapters"
        @select="handleChapterSelect"
        @create="handleChapterCreate"
        @edit="handleChapterEdit"
        @delete="handleChapterDelete"
        @load-more="loadMoreChapters"
      />

      <!-- 中间：段落编辑器 -->
      <ParagraphStream
        :paragraphs="paragraphs"
        :selected-id="selectedParagraphId"
        :loading="paragraphsLoading"
        @select="handleParagraphSelect"
        @update="handleParagraphUpdate"
        @create="handleParagraphCreate"
        @physical-delete="handleParagraphPhysicalDelete"
      />

      <!-- 右侧：句子检查器 -->
      <SentenceInspector
        :paragraph="selectedParagraph"
        :loading="sentencesLoading"
      />
    </div>

    <!-- 章节编辑对话框 -->
    <ChapterFormDialog
      v-model="showChapterDialog"
      :chapter="editingChapter"
      @submit="handleChapterSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check } from '@element-plus/icons-vue'
import { useProjectsStore } from '@/stores/projects'

import ChapterNav from '@/components/studio/ChapterNav.vue'
import ParagraphStream from '@/components/studio/ParagraphStream.vue'
import SentenceInspector from '@/components/studio/SentenceInspector.vue'
import ChapterFormDialog from '@/components/studio/ChapterFormDialog.vue'

import chaptersService from '@/services/chapters'
import paragraphsService from '@/services/paragraphs'

const router = useRouter()
const route = useRoute()

// Props
const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

// 状态
const projectTitle = ref('')
const project = ref(null)  // 添加项目数据
const chapters = ref([])
const paragraphs = ref([])
const selectedChapterId = ref(null)
const selectedParagraphId = ref(null)
const selectedParagraph = computed(() => 
  paragraphs.value.find(p => p.id === selectedParagraphId.value)
)

// 章节对话框状态
const showChapterDialog = ref(false)
const editingChapter = ref(null)

// 加载状态
const chaptersLoading = ref(false)
const paragraphsLoading = ref(false)
const sentencesLoading = ref(false)
const saving = ref(false)

// 修改追踪
const modifiedParagraphs = ref(new Map())
const hasChanges = computed(() => modifiedParagraphs.value.size > 0)

// 加载项目信息
const loadProject = async () => {
  try {
    const projectsStore = useProjectsStore()
    project.value = await projectsStore.getProject(props.projectId)
    projectTitle.value = project.value?.title || ''
  } catch (error) {
    console.error('加载项目信息失败:', error)
  }
}

// 加载章节列表
const currentPage = ref(1)
const pageSize = ref(100)  // 每页100个章节（后端最大限制）
const hasMoreChapters = ref(true)

const loadChapters = async (reset = false) => {
  try {
    chaptersLoading.value = true
    
    if (reset) {
      currentPage.value = 1
      chapters.value = []
    }
    
    // 后端API使用 size 参数，不是 page_size
    const response = await chaptersService.getChapters(props.projectId, {
      page: currentPage.value,
      size: pageSize.value  // 使用 size 而不是 page_size
    })
    
    const newChapters = response.chapters || []
    
    if (reset) {
      chapters.value = newChapters
    } else {
      chapters.value = [...chapters.value, ...newChapters]
    }
    
    // 检查是否还有更多章节
    // 如果返回的章节数少于请求的数量，说明没有更多了
    hasMoreChapters.value = newChapters.length >= pageSize.value
    
    console.log('章节加载:', {
      currentPage: currentPage.value,
      loaded: newChapters.length,
      total: chapters.value.length,
      hasMore: hasMoreChapters.value
    })
    
    // 自动选中第一章（仅在首次加载时）
    if (reset && chapters.value.length > 0 && !selectedChapterId.value) {
      selectedChapterId.value = chapters.value[0].id
      await loadParagraphs(chapters.value[0].id)
    }
  } catch (error) {
    console.error('加载章节失败:', error)
    ElMessage.error('加载章节失败')
  } finally {
    chaptersLoading.value = false
  }
}

// 加载更多章节
const loadMoreChapters = async () => {
  if (!hasMoreChapters.value || chaptersLoading.value) return
  currentPage.value++
  await loadChapters(false)
}

// 加载段落列表
const loadParagraphs = async (chapterId) => {
  try {
    paragraphsLoading.value = true
    const response = await paragraphsService.getParagraphs(chapterId)
    paragraphs.value = response.paragraphs || []
  } catch (error) {
    console.error('加载段落失败:', error)
    ElMessage.error('加载段落失败')
  } finally {
    paragraphsLoading.value = false
  }
}

// 事件处理
const handleChapterSelect = async (chapterId) => {
  if (selectedChapterId.value === chapterId) return
  
  // 如果有未保存的修改，提示用户
  if (hasChanges.value) {
    try {
      await ElMessageBox.confirm(
        '当前有未保存的修改，切换章节将丢失这些修改。是否继续？',
        '提示',
        {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      modifiedParagraphs.value.clear()
    } catch {
      return
    }
  }
  
  selectedChapterId.value = chapterId
  selectedParagraphId.value = null
  await loadParagraphs(chapterId)
}

const handleParagraphSelect = (paragraphId) => {
  selectedParagraphId.value = paragraphId
}

const handleParagraphUpdate = (paragraphId, updates) => {
  // 找到段落对象并更新
  const paragraph = paragraphs.value.find(p => p.id === paragraphId)
  if (paragraph) {
    // 直接更新段落对象以触发响应式更新
    Object.assign(paragraph, updates)
  }
  
  // 同时记录到修改Map中
  modifiedParagraphs.value.set(paragraphId, {
    ...modifiedParagraphs.value.get(paragraphId),
    ...updates
  })
}

// 创建段落
const handleParagraphCreate = async (paragraphData) => {
  if (!selectedChapterId.value) {
    ElMessage.warning('请先选择一个章节')
    return
  }

  try {
    await paragraphsService.createParagraph(selectedChapterId.value, paragraphData)
    ElMessage.success('段落创建成功')
    // 重新加载段落列表
    await loadParagraphs(selectedChapterId.value)
  } catch (error) {
    console.error('创建段落失败:', error)
    ElMessage.error('创建段落失败')
  }
}

// 立即物理删除段落
const handleParagraphPhysicalDelete = async (paragraphId) => {
  try {
    await paragraphsService.deleteParagraph(paragraphId)
    ElMessage.success('段落删除成功')
    // 重新加载段落列表
    if (selectedChapterId.value) {
      await loadParagraphs(selectedChapterId.value)
    }
  } catch (error) {
    console.error('删除段落失败:', error)
    ElMessage.error('删除段落失败')
  }
}

// 统计信息计算属性 - 从项目数据获取
const totalParagraphs = computed(() => {
  return project.value?.paragraph_count || 0
})

const totalWords = computed(() => {
  return project.value?.word_count || 0
})

const totalChapters = computed(() => {
  return project.value?.chapter_count || chapters.value.length
})

// 章节管理
const handleChapterCreate = () => {
  editingChapter.value = null
  showChapterDialog.value = true
}

const handleChapterEdit = (chapter) => {
  editingChapter.value = chapter
  showChapterDialog.value = true
}

const handleChapterDelete = async (chapter) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除章节"${chapter.title}"吗？这将同时删除该章节下的所有段落。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const wasCurrentChapter = selectedChapterId.value === chapter.id
    
    await chaptersService.deleteChapter(chapter.id)
    ElMessage.success('章节删除成功')
    
    // 重新加载章节列表
    await loadChapters()
    
    // 如果删除的是当前选中的章节
    if (wasCurrentChapter) {
      // 尝试选择下一个章节
      if (chapters.value.length > 0) {
        selectedChapterId.value = chapters.value[0].id
        await loadParagraphs(chapters.value[0].id)
      } else {
        // 如果没有章节了，清空
        selectedChapterId.value = null
        paragraphs.value = []
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除章节失败:', error)
      ElMessage.error('删除章节失败')
    }
  }
}

const handleChapterSubmit = async (chapterData) => {
  try {
    const isEditingCurrentChapter = chapterData.id === selectedChapterId.value
    
    if (chapterData.id) {
      // 编辑
      await chaptersService.updateChapter(chapterData.id, chapterData)
      ElMessage.success('章节更新成功')
    } else {
      // 创建
      await chaptersService.createChapter(props.projectId, chapterData)
      ElMessage.success('章节创建成功')
    }
    
    // 重新加载章节列表
    await loadChapters()
    
    // 如果编辑的是当前选中的章节，需要重新加载段落列表
    // 因为章节内容可能改变，段落会重新解析
    if (isEditingCurrentChapter && selectedChapterId.value) {
      await loadParagraphs(selectedChapterId.value)
    }
  } catch (error) {
    console.error('保存章节失败:', error)
    ElMessage.error('保存章节失败')
  }
}

const handleSave = async () => {
  if (!hasChanges.value || !selectedChapterId.value) return
  
  try {
    saving.value = true
    
    // 分离编辑和删除的段落
    const toUpdate = []
    const toDelete = []
    
    modifiedParagraphs.value.forEach((changes, paragraphId) => {
      if (changes.action === 'delete') {
        // 标记为删除
        toDelete.push(paragraphId)
      } else if (changes.action === 'edit' && changes.edited_content) {
        // 更新内容
        toUpdate.push({
          id: paragraphId,
          content: changes.edited_content
        })
      }
    })
    
    // 执行删除操作（物理删除）
    for (const paragraphId of toDelete) {
      await paragraphsService.deleteParagraph(paragraphId)
    }
    
    // 执行更新操作
    for (const update of toUpdate) {
      await paragraphsService.updateParagraph(update.id, {
        content: update.content
      })
    }
    
    const message = `保存成功：${toUpdate.length > 0 ? `编辑${toUpdate.length}个` : ''}${toUpdate.length > 0 && toDelete.length > 0 ? '，' : ''}${toDelete.length > 0 ? `删除${toDelete.length}个` : ''}`
    ElMessage.success(message || '保存成功')
    
    // 清空修改记录
    modifiedParagraphs.value.clear()
    
    // 重新加载段落列表
    await loadParagraphs(selectedChapterId.value)
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleBack = () => {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      '当前有未保存的修改，返回将丢失这些修改。是否继续？',
      '提示',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      router.push({ name: 'Projects' })
    }).catch(() => {})
  } else {
    router.push({ name: 'Projects' })
  }
}

// 路由守卫
onBeforeRouteLeave((to, from, next) => {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      '当前有未保存的修改，离开将丢失这些修改。是否继续？',
      '提示',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      next()
    }).catch(() => {
      next(false)
    })
  } else {
    next()
  }
})

// 生命周期
onMounted(async () => {
  await loadProject()
  await loadChapters(true)  // reset=true 首次加载
})
</script>

<style scoped>
.content-studio {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.studio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.project-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.studio-stats {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  min-width: 100px;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--primary-color);
}

.studio-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
</style>
