<template>
  <div 
    class="director-mode"
    v-loading="loading || isPolling"
    :element-loading-text="loadingText"
    element-loading-background="rgba(255, 255, 255, 0.8)"
  >
    <!-- 任务完成统计信息 -->
    <div v-if="taskCompletionStats" class="task-completion-alert">
      <el-alert
        :title="taskCompletionStats.title"
        :type="taskCompletionStats.type"
        :closable="true"
        @close="taskCompletionStats = null"
        show-icon
      >
        <template #default>
          <div class="stats-content">
            <p v-html="taskCompletionStats.message"></p>
          </div>
        </template>
      </el-alert>
    </div>

    <div class="toolbar">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="选择章节" style="width: 240px">
          <el-select v-model="selectedChapterId" placeholder="请选择已确认的章节" @change="loadSentences">
            <el-option
              v-for="chapter in chapters"
              :key="chapter.id"
              :label="`第${chapter.chapter_number}章: ${chapter.title}`"
              :value="chapter.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="提示词" style="width: 120px">
          <el-select v-model="filterHasPrompt" placeholder="全部" clearable @change="loadSentences">
            <el-option label="已生成" value="true" />
            <el-option label="未生成" value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="图片" style="width: 120px">
          <el-select v-model="filterHasImage" placeholder="全部" clearable @change="loadSentences">
            <el-option label="已生成" value="true" />
            <el-option label="未生成" value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="音频" style="width: 120px">
          <el-select v-model="filterHasAudio" placeholder="全部" clearable @change="loadSentences">
            <el-option label="已生成" value="true" />
            <el-option label="未生成" value="false" />
          </el-select>
        </el-form-item>
        
        <div class="action-buttons" v-if="selectedChapterId">
          <el-button type="primary" @click="generatePromptsVisible = true">
            批量生成提示词
          </el-button>
          <el-button type="warning"  @click="batchGenerateImagesVisible = true">
            批量生成图片
          </el-button>
          <el-button type="success"  @click="batchGenerateAudioVisible = true">
            批量生成音频
          </el-button>
          <el-button type="info" @click="handleCheckMaterials" :loading="checkingMaterials">
            <el-icon><DocumentChecked /></el-icon>
            检测素材
          </el-button>
          <el-button type="primary" plain @click="handleExportToJianYing" :loading="exportingToJianYing" :disabled="!isMaterialsReady">
            <el-icon><Download /></el-icon>
            导出剪映
          </el-button>
        </div>
      </el-form>
      
      <!-- 生成提示词对话框 -->
      <GeneratePromptsDialog
        v-model:visible="generatePromptsVisible"
        :chapter-id="selectedChapterId"
        :api-keys="apiKeys"
        @generate-success="(taskId) => handleGenerateSuccess(taskId, 'prompts')"
      />
      
      <!-- 重新生成提示词对话框 -->
      <RegeneratePromptsDialog
        v-model:visible="regeneratePromptsVisible"
        :sentence-ids="selectedSentenceIds"
        :api-keys="apiKeys"
        @regenerate-success="handleRegenerateSuccess"
      />
      
      <!-- 批量生成图片对话框 -->
      <BatchGenerateImagesDialog
        v-model:visible="batchGenerateImagesVisible"
        :sentences-ids="singleImageSentenceId ? [singleImageSentenceId] : currentChapterSentenceIds"
        :api-keys="apiKeys"
        @generate-success="(taskId) => handleGenerateSuccess(taskId, 'images')"
        @update:visible="(val) => { if(!val) singleImageSentenceId = null }"
      />

      <!-- 批量生成音频对话框 -->
      <GenerateAudioDialog
        v-model:visible="batchGenerateAudioVisible"
        :sentences-ids="singleAudioSentenceId ? [singleAudioSentenceId] : currentChapterSentenceIds"
        :api-keys="apiKeys"
        @generate-success="(taskId) => handleGenerateSuccess(taskId, 'audio')"
        @update:visible="(val) => { if(!val) singleAudioSentenceId = null }"
      />
    </div>

    <div class="content-area">
      <el-empty v-if="!sentences.length" description="暂无数据" />
      
      <div v-else class="card-grid">
        <SentenceCard
          v-for="(sentence, index) in sentences"
          :key="sentence.id"
          :sentence="sentence"
          :index="index"
          :loading-states="loadingStates[sentence.id]"
          @prompt-action="handlePromptAction"
          @regenerate-prompt="handleRegeneratePrompt"
          @preview="handlePreview"
          @regenerate-image="handleRegenerateImage"
          @generate-audio="handleGenerateAudio"
          @update:loading-states="(newState) => updateSentenceLoadingState(sentence.id, newState)"
        />
      </div>
    </div>
    
    <!-- 查看/编辑提示词对话框 - 使用新组件 -->
    <PromptDialog
      v-model:visible="promptDialogVisible"
      v-model:sentence="currentSentence"
      :is-editing="isEditingPrompt"
      :dialog-title="promptDialogTitle"
      @save="handlePromptSave"
    />
    
    <!-- 素材检测对话框 -->
    <MaterialCheckDialog
      v-model:visible="materialCheckVisible"
      :loading="checkingMaterials"
      :result="materialCheckResult"
      @generate="handleGenerateMissingMaterials"
    />
    
    <!-- 素材预览对话框 -->
    <MaterialPreviewDialog
      v-model:visible="previewDialogVisible"
      :type="previewType"
      :content="previewContent"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useDirectorEngine } from '@/composables/useDirectorEngine'
import { useTaskPoller } from '@/composables/useTaskPoller'
import GeneratePromptsDialog from '@/components/studio/GeneratePromptsDialog.vue'
import RegeneratePromptsDialog from '@/components/studio/RegeneratePromptsDialog.vue'
import BatchGenerateImagesDialog from '@/components/studio/BatchGenerateImagesDialog.vue'
import GenerateAudioDialog from '@/components/studio/GenerateAudioDialog.vue'
import SentenceCard from '@/components/studio/SentenceCard.vue'
import PromptDialog from '@/components/studio/PromptDialog.vue'
import MaterialCheckDialog from '@/components/studio/MaterialCheckDialog.vue'
import MaterialPreviewDialog from '@/components/studio/MaterialPreviewDialog.vue'
import { DocumentChecked, Download } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

// 使用 composable 管理状态和逻辑
const {
  chapters,
  apiKeys,
  sentences,
  selectedChapterId,
  loading,
  loadingStates,
  filterHasPrompt,
  filterHasImage,
  filterHasAudio,
  generatePromptsVisible,
  regeneratePromptsVisible,
  batchGenerateImagesVisible,
  batchGenerateAudioVisible,
  selectedSentenceIds,
  loadSentences,
  updateSentenceLoadingState,
  handlePromptAction: fetchPromptAction
} = useDirectorEngine(props.projectId)

const {
  taskStatus,
  isPolling,
  taskStatistics,
  startPolling
} = useTaskPoller()

// 任务完成统计信息
const taskCompletionStats = ref(null)

// 素材检测状态
const checkingMaterials = ref(false)
const materialCheckVisible = ref(false)
const materialCheckResult = ref(null)

// 导出状态
const exportingToJianYing = ref(false)

// 计算素材是否准备就绪
const isMaterialsReady = computed(() => {
  return materialCheckResult.value?.all_ready || false
})

// 预览状态
const previewDialogVisible = ref(false)
const previewType = ref('prompt')
const previewContent = ref('')

// 加载文本
const loadingText = computed(() => {
  if (isPolling.value) {
    return '任务执行中，请耐心等待，不要关闭页面...'
  }
  return '加载中...'
})

// 提示词对话框状态
const promptDialogVisible = ref(false)
const promptDialogTitle = ref('')
const currentSentence = ref({})
const isEditingPrompt = ref(false)

// 计算当前章节的句子ID列表
const currentChapterSentenceIds = computed(() => {
  return sentences.value.map(sentence => sentence.id)
})

// 显示任务统计信息
const showTaskStatistics = (statistics, taskType) => {
  if (!statistics) return
  
  const { total, success, failed } = statistics
  const isSuccess = failed === 0
  
  let message = ''
  if (taskType === 'prompts') {
    message = `<strong>提示词生成完成</strong><br/>
      总计: ${total} 条<br/>
      成功: <span style="color: #67C23A">${success}</span> 条<br/>
      失败: <span style="color: #F56C6C">${failed}</span> 条`
  } else if (taskType === 'images') {
    message = `<strong>图片生成完成</strong><br/>
      总计: ${total} 张<br/>
      成功: <span style="color: #67C23A">${success}</span> 张<br/>
      失败: <span style="color: #F56C6C">${failed}</span> 张`
  } else if (taskType === 'audio') {
    message = `<strong>音频生成完成</strong><br/>
      总计: ${total} 条<br/>
      成功: <span style="color: #67C23A">${success}</span> 条<br/>
      失败: <span style="color: #F56C6C">${failed}</span> 条`
  }
  
  taskCompletionStats.value = {
    title: isSuccess ? '任务成功完成' : '任务完成（部分失败）',
    type: isSuccess ? 'success' : 'warning',
    message
  }
}

// 显示任务错误信息
const showTaskError = (errorResult) => {
  const errorMessage = errorResult?.message || '任务执行失败'
  const errorType = errorResult?.error || 'Error'
  
  taskCompletionStats.value = {
    title: '任务执行失败',
    type: 'error',
    message: `<strong>错误类型:</strong> ${errorType}<br/><strong>错误信息:</strong> ${errorMessage}`
  }
}

// 处理生成成功
const handleGenerateSuccess = async (taskId, taskType = 'prompts') => {
  if (taskId) {
    // 显示任务提交提示
    ElNotification({
      title: '任务已提交',
      message: '任务正在后台执行，预计需要几分钟时间，请不要关闭页面',
      type: 'info',
      duration: 5000
    })
    
    startPolling(
      taskId,
      async (statistics) => {
        showTaskStatistics(statistics, taskType)
        await loadSentences()
      },
      (errorResult) => {
        showTaskError(errorResult)
      }
    )
  } else {
    // Fallback for immediate success (if any)
    await loadSentences()
  }
}

// 处理重新生成成功
const handleRegenerateSuccess = async (taskId) => {
  if (taskId) {
    ElNotification({
      title: '任务已提交',
      message: '重新生成任务正在后台执行，请不要关闭页面',
      type: 'info',
      duration: 5000
    })
    
    startPolling(
      taskId,
      async (statistics) => {
        showTaskStatistics(statistics, 'prompts')
        await loadSentences()
      },
      (errorResult) => {
        showTaskError(errorResult)
      }
    )
  } else {
    await loadSentences()
  }
}

// 处理提示词操作（查看/编辑）
const handlePromptAction = async (event) => {
  const { action, sentence } = event
  const result = await fetchPromptAction(action, sentence)
  
  if (result) {
    currentSentence.value = { ...result.sentence }
    if (action === 'view') {
      promptDialogTitle.value = '查看提示词'
      isEditingPrompt.value = false
    } else if (action === 'edit') {
      promptDialogTitle.value = '编辑提示词'
      isEditingPrompt.value = true
    }
    promptDialogVisible.value = true
  }
}

// 处理重新生成提示词
const handleRegeneratePrompt = (sentence) => {
  // 设置当前句子ID
  selectedSentenceIds.value = [sentence.id]
  // 打开重新生成提示词对话框
  regeneratePromptsVisible.value = true
}

// 处理重新生成图片
const handleRegenerateImage = (sentence) => {
  // We will use a temporary state for single image generation
  singleImageSentenceId.value = sentence.id
  batchGenerateImagesVisible.value = true
}

const singleImageSentenceId = ref(null)
const singleAudioSentenceId = ref(null)

// 处理生成音频
const handleGenerateAudio = (sentence) => {
  singleAudioSentenceId.value = sentence.id
  batchGenerateAudioVisible.value = true
}

// 处理提示词保存
const handlePromptSave = (updatedSentence) => {
  // 更新原句子的提示词
  const index = sentences.value.findIndex(s => s.id === updatedSentence.id)
  if (index !== -1) {
    sentences.value[index].image_prompt = updatedSentence.image_prompt
  }
}

// 处理检测素材
const handleCheckMaterials = async () => {
  if (!selectedChapterId.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  
  checkingMaterials.value = true
  materialCheckResult.value = null
  
  try {
    const { chaptersService } = await import('@/services/chapters')
    const response = await chaptersService.checkChapterMaterials(selectedChapterId.value)

    materialCheckResult.value = response
    materialCheckVisible.value = true
    
    // 如果所有素材都准备好，显示成功消息
    if (response.all_ready) {
      ElMessage.success('所有素材已准备就绪，章节状态已更新')
      // 重新加载句子列表以更新状态
      await loadSentences()
    }
  } catch (error) {
    console.error('检测素材失败:', error)
    ElMessage.error('检测素材失败，请重试')
  } finally {
    checkingMaterials.value = false
  }
}

// 处理生成缺失的素材
const handleGenerateMissingMaterials = () => {
  // 这里可以根据缺失的素材类型打开相应的生成对话框
  ElMessage.info('请使用批量生成按钮生成缺失的素材')
}

// 处理预览
const handlePreview = ({ type, content }) => {
  if (!content) {
    ElMessage.warning('暂无可预览的内容')
    return
  }
  
  previewType.value = type
  previewContent.value = content
  previewDialogVisible.value = true
}

// 处理导出到剪映
const handleExportToJianYing = async () => {
  if (!selectedChapterId.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  
  if (!isMaterialsReady.value) {
    ElMessage.warning('请先检测素材，确保所有素材已准备就绪')
    return
  }
  
  exportingToJianYing.value = true
  
  try {
    const exportService = await import('@/services/export')
    const response = await exportService.default.exportToJianYing(selectedChapterId.value)
    
    if (response.success) {
      ElMessage.success('导出成功，开始下载...')
      
      // 触发文件下载 - response.download_url 已经包含完整路径
      try {
        await exportService.default.downloadFile(response.download_url, response.filename)
        ElMessage.success('文件下载完成')
      } catch (downloadError) {
        console.error('下载文件失败:', downloadError)
        ElMessage.error('文件下载失败，请重试')
      }
    } else {
      ElMessage.error(response.message || '导出失败')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    exportingToJianYing.value = false
  }
}
</script>

<style scoped>
/* 页面基础样式 */
.director-mode {
  padding: var(--space-lg);
}

/* 任务完成提示样式 */
.task-completion-alert {
  margin-bottom: var(--space-lg);
}

.stats-content {
  line-height: 1.8;
}

/* 工具栏样式 */
.toolbar {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  box-shadow: var(--shadow-sm);
}

/* 内容区域样式 */
.content-area {
  margin-top: var(--space-lg);
}

/* 卡片网格样式 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--space-lg);
}

/* 表单样式 */
.filter-form {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.filter-form .el-form-item {
  margin-bottom: 0;
}

.action-buttons {
  display: flex;
  gap: var(--space-sm);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr;
    gap: var(--space-md);
  }

  .filter-form {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>