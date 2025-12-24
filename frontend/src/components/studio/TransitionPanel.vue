<template>
  <div class="transition-panel">
    <div class="panel-header">
      <h3>过渡视频</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="creating"
          :disabled="!canCreate"
          @click="handleCreateClick"
        >
          批量创建
        </el-button>
        <el-button 
          type="success"
          :loading="generating"
          :disabled="transitions.length === 0"
          @click="handleBatchGenerateClick"
        >
          批量生成视频
        </el-button>
      </div>
    </div>

    <div class="transition-list">
      <el-empty v-if="transitions.length === 0" description="暂无过渡，请先创建过渡" />
      
      <div v-else class="transition-grid">
        <div 
          v-for="transition in transitions" 
          :key="transition.id"
          class="transition-card"
        >
          <div class="transition-header">
            <span class="transition-number">过渡 {{ transition.order_index }}</span>
            <div class="transition-actions">
              <el-button
                v-if="!transition.video_url"
                type="success"
                size="small"
                :loading="generatingIds.has(transition.id)"
                :disabled="generatingIds.has(transition.id)"
                @click="handleGenerateVideo(transition)"
              >
                生成视频
              </el-button>
              <el-button
                v-else
                type="warning"
                size="small"
                :loading="generatingIds.has(transition.id)"
                :disabled="generatingIds.has(transition.id)"
                @click="handleRegenerateVideo(transition)"
              >
                重新生成
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="handleEditPrompt(transition)"
              >
                编辑提示词
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(transition)"
              >
                删除
              </el-button>
            </div>
          </div>
          
          <div class="transition-content">
            <div class="shot-info">
              <span class="label">起始镜头:</span>
              <span class="value">{{ getShotDescription(transition.from_shot_id) }}</span>
            </div>
            <div class="shot-info">
              <span class="label">结束镜头:</span>
              <span class="value">{{ getShotDescription(transition.to_shot_id) }}</span>
            </div>
            <div class="prompt-preview">
              <span class="label">提示词:</span>
              <p class="prompt-text">{{ transition.video_prompt || '未生成' }}</p>
            </div>
          </div>

          <div v-if="transition.video_url" class="transition-video">
            <video :src="transition.video_url" controls />
          </div>
          <div v-else-if="transition.status === 'processing'" class="transition-placeholder">
            <el-icon :size="40"><Loading /></el-icon>
            <p>生成中...</p>
          </div>
          <div v-else class="transition-placeholder">
            <el-icon :size="40"><VideoCamera /></el-icon>
            <p>待生成</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量创建对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="批量创建过渡"
      width="500px"
    >
      <el-form :model="createFormData" label-width="100px">
        <el-form-item label="API Key">
          <el-select v-model="createFormData.apiKeyId" placeholder="请选择API Key" style="width: 100%">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="`${key.name} (${key.provider})`"
              :value="key.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="文本模型">
          <el-select 
            v-model="createFormData.model" 
            placeholder="选择模型" 
            style="width: 100%"
            :loading="loadingTextModels"
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="model in textModelOptions"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateConfirm" :disabled="!createFormData.apiKeyId || !createFormData.model">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量生成视频对话框 -->
    <el-dialog
      v-model="showBatchGenerateDialog"
      title="批量生成过渡视频"
      width="500px"
    >
      <el-form :model="batchGenerateFormData" label-width="100px">
        <el-form-item label="API Key">
          <el-select v-model="batchGenerateFormData.apiKeyId" placeholder="请选择API Key" style="width: 100%">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="`${key.name} (${key.provider})`"
              :value="key.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="视频模型">
          <el-select 
            v-model="batchGenerateFormData.videoModel" 
            placeholder="选择模型" 
            style="width: 100%"
            :loading="loadingVideoModels"
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="model in videoModelOptions"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchGenerateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchGenerateConfirm" :disabled="!batchGenerateFormData.apiKeyId || !batchGenerateFormData.videoModel">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑提示词对话框 -->
    <el-dialog
      v-model="showEditPromptDialog"
      title="编辑过渡提示词"
      width="700px"
    >
      <el-form :model="editPromptFormData" label-width="100px">
        <el-form-item label="视频提示词">
          <el-input
            v-model="editPromptFormData.prompt"
            type="textarea"
            :rows="12"
            placeholder="视频生成提示词"
            style="font-family: monospace; font-size: 12px;"
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            💡 提示词用于生成两个分镜之间的过渡视频。您可以根据需要调整。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditPromptDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEditPromptConfirm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 单个生成视频对话框 -->
    <el-dialog
      v-model="showSingleGenerateDialog"
      :title="singleGenerateDialogType === 'generate' ? '生成过渡视频' : '重新生成过渡视频'"
      width="700px"
    >
      <el-form :model="singleGenerateFormData" label-width="100px">
        <el-form-item label="API Key">
          <el-select v-model="singleGenerateFormData.apiKeyId" placeholder="请选择API Key" style="width: 100%">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="`${key.name} (${key.provider})`"
              :value="key.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="视频模型">
          <el-select 
            v-model="singleGenerateFormData.videoModel" 
            placeholder="选择模型" 
            style="width: 100%"
            :loading="loadingVideoModels"
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="model in videoModelOptions"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="视频提示词">
          <el-input
            v-model="singleGenerateFormData.prompt"
            type="textarea"
            :rows="12"
            placeholder="视频生成提示词（可编辑调整）"
            style="font-family: monospace; font-size: 12px;"
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px;">
            💡 提示词用于生成两个分镜之间的过渡视频。您可以根据需要调整。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSingleGenerateDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSingleGenerateConfirm" 
          :disabled="!singleGenerateFormData.apiKeyId || !singleGenerateFormData.videoModel"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, VideoCamera } from '@element-plus/icons-vue'
import { useTransitionWorkflow } from '@/composables/useTransitionWorkflow'
import api from '@/services/api'

const props = defineProps({
  scriptId: String,
  apiKeys: Array
})

const {
  transitions,
  creating,
  generating,
  generatingIds,
  loadTransitions,
  createTransitions,
  generateTransitionVideos,
  updateTransitionPrompt,
  generateSingleVideo,
  deleteTransition
} = useTransitionWorkflow()

// 对话框状态
const showCreateDialog = ref(false)
const showBatchGenerateDialog = ref(false)
const showEditPromptDialog = ref(false)
const showSingleGenerateDialog = ref(false)
const singleGenerateDialogType = ref('generate')

// 表单数据
const createFormData = ref({
  apiKeyId: '',
  model: ''
})

const batchGenerateFormData = ref({
  apiKeyId: '',
  videoModel: 'veo_3_1-fast'
})

const editPromptFormData = ref({
  transitionId: '',
  prompt: ''
})

const singleGenerateFormData = ref({
  transitionId: '',
  apiKeyId: '',
  videoModel: 'veo_3_1-fast',
  prompt: ''
})

// 模型选项
const textModelOptions = ref([])
const videoModelOptions = ref([])
const loadingTextModels = ref(false)
const loadingVideoModels = ref(false)

// 计算属性
const canCreate = computed(() => {
  return props.apiKeys && props.apiKeys.length > 0
})

// 监听API Key变化加载模型
watch(() => createFormData.value.apiKeyId, async (newKeyId) => {
  if (!newKeyId) {
    textModelOptions.value = []
    createFormData.value.model = ''
    return
  }
  
  loadingTextModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=text`)
    textModelOptions.value = models || []
    if (textModelOptions.value.length > 0) {
      createFormData.value.model = textModelOptions.value[0]
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    textModelOptions.value = []
    createFormData.value.model = ''
  } finally {
    loadingTextModels.value = false
  }
})

watch(() => batchGenerateFormData.value.apiKeyId, async (newKeyId) => {
  if (!newKeyId) {
    videoModelOptions.value = []
    batchGenerateFormData.value.videoModel = 'veo_3_1-fast'
    return
  }
  
  loadingVideoModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=video`)
    videoModelOptions.value = models || []
    if (videoModelOptions.value.length > 0) {
      batchGenerateFormData.value.videoModel = videoModelOptions.value[0]
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    videoModelOptions.value = ['veo_3_1-fast']
    batchGenerateFormData.value.videoModel = 'veo_3_1-fast'
  } finally {
    loadingVideoModels.value = false
  }
})

watch(() => singleGenerateFormData.value.apiKeyId, async (newKeyId) => {
  if (!newKeyId) {
    videoModelOptions.value = []
    singleGenerateFormData.value.videoModel = 'veo_3_1-fast'
    return
  }
  
  loadingVideoModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=video`)
    videoModelOptions.value = models || []
    if (videoModelOptions.value.length > 0) {
      singleGenerateFormData.value.videoModel = videoModelOptions.value[0]
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    videoModelOptions.value = ['veo_3_1-fast']
    singleGenerateFormData.value.videoModel = 'veo_3_1-fast'
  } finally {
    loadingVideoModels.value = false
  }
})

// 加载transitions
watch(() => props.scriptId, (newId) => {
  if (newId) {
    loadTransitions(newId)
  }
}, { immediate: true })

// 辅助函数
const getShotDescription = (shotId) => {
  // TODO: 从shots数据中获取描述
  return `镜头 ${shotId.substring(0, 8)}...`
}

// 批量创建
const handleCreateClick = () => {
  createFormData.value = {
    apiKeyId: props.apiKeys[0]?.id || '',
    model: ''
  }
  showCreateDialog.value = true
}

const handleCreateConfirm = async () => {
  if (!createFormData.value.apiKeyId || !createFormData.value.model) {
    return
  }
  await createTransitions(props.scriptId, createFormData.value.apiKeyId, createFormData.value.model)
  showCreateDialog.value = false
}

// 批量生成
const handleBatchGenerateClick = () => {
  batchGenerateFormData.value = {
    apiKeyId: props.apiKeys[0]?.id || '',
    videoModel: 'veo_3_1-fast'
  }
  showBatchGenerateDialog.value = true
}

const handleBatchGenerateConfirm = async () => {
  if (!batchGenerateFormData.value.apiKeyId || !batchGenerateFormData.value.videoModel) {
    return
  }
  await generateTransitionVideos(props.scriptId, batchGenerateFormData.value.apiKeyId, batchGenerateFormData.value.videoModel)
  showBatchGenerateDialog.value = false
}

// 编辑提示词
const handleEditPrompt = (transition) => {
  editPromptFormData.value = {
    transitionId: transition.id,
    prompt: transition.video_prompt || ''
  }
  showEditPromptDialog.value = true
}

const handleEditPromptConfirm = async () => {
  const success = await updateTransitionPrompt(
    editPromptFormData.value.transitionId,
    editPromptFormData.value.prompt
  )
  if (success) {
    await loadTransitions(props.scriptId)
    showEditPromptDialog.value = false
  }
}

// 单个生成
const handleGenerateVideo = (transition) => {
  singleGenerateDialogType.value = 'generate'
  singleGenerateFormData.value = {
    transitionId: transition.id,
    apiKeyId: props.apiKeys[0]?.id || '',
    videoModel: 'veo_3_1-fast',
    prompt: transition.video_prompt || ''
  }
  showSingleGenerateDialog.value = true
}

const handleRegenerateVideo = (transition) => {
  singleGenerateDialogType.value = 'regenerate'
  singleGenerateFormData.value = {
    transitionId: transition.id,
    apiKeyId: props.apiKeys[0]?.id || '',
    videoModel: 'veo_3_1-fast',
    prompt: transition.video_prompt || ''
  }
  showSingleGenerateDialog.value = true
}

const handleSingleGenerateConfirm = async () => {
  if (!singleGenerateFormData.value.apiKeyId || !singleGenerateFormData.value.videoModel) {
    return
  }
  await generateSingleVideo(
    singleGenerateFormData.value.transitionId,
    props.scriptId,
    singleGenerateFormData.value.apiKeyId,
    singleGenerateFormData.value.videoModel,
    singleGenerateFormData.value.prompt
  )
  showSingleGenerateDialog.value = false
}

// 删除
const handleDelete = async (transition) => {
  try {
    await ElMessageBox.confirm('确定要删除这个过渡吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTransition(transition.id, props.scriptId)
  } catch (error) {
    // 用户取消
  }
}
</script>

<style scoped>
.transition-panel {
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 12px;
}

.transition-list {
  margin-top: 20px;
}

.transition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.transition-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
  background: white;
}

.transition-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.transition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
}

.transition-number {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
  flex-shrink: 0;
}

.transition-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.transition-content {
  margin-bottom: 12px;
}

.shot-info {
  margin-bottom: 8px;
  font-size: 13px;
}

.shot-info .label {
  font-weight: 600;
  color: #606266;
  margin-right: 8px;
}

.shot-info .value {
  color: #909399;
}

.prompt-preview {
  margin-top: 12px;
}

.prompt-preview .label {
  font-weight: 600;
  color: #606266;
  display: block;
  margin-bottom: 4px;
}

.prompt-text {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin: 0;
  max-height: 60px;
  overflow-y: auto;
  font-family: monospace;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
}

.transition-video {
  margin-top: 12px;
}

.transition-video video {
  width: 100%;
  border-radius: 4px;
  background: #000;
}

.transition-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
  margin-top: 12px;
}

.transition-placeholder p {
  margin-top: 8px;
  font-size: 13px;
}
</style>
