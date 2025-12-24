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
          创建过渡
        </el-button>
        <el-button 
          type="success"
          :loading="generating"
          :disabled="transitions.length === 0"
          @click="handleGenerateClick"
        >
          生成视频
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
            <el-tag v-if="transition.video_url" type="success" size="small">已生成</el-tag>
            <el-tag v-else-if="transition.status === 'processing'" type="warning" size="small">生成中</el-tag>
            <el-tag v-else type="info" size="small">待生成</el-tag>
          </div>
          
          <div class="transition-content">
            <p class="transition-prompt">{{ transition.video_prompt }}</p>
          </div>

          <div v-if="transition.video_url" class="transition-video">
            <video :src="transition.video_url" controls />
          </div>
        </div>
      </div>
    </div>

    <!-- 创建过渡对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建过渡"
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

    <!-- 生成视频对话框 -->
    <el-dialog
      v-model="showGenerateDialog"
      title="生成过渡视频"
      width="500px"
    >
      <el-form :model="generateFormData" label-width="100px">
        <el-form-item label="API Key">
          <el-select v-model="generateFormData.apiKeyId" placeholder="请选择API Key" style="width: 100%">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="`${key.name} (${key.provider})`"
              :value="key.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="视频模型">
          <el-input v-model="generateFormData.videoModel" placeholder="请输入视频模型名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleGenerateConfirm" :disabled="!generateFormData.apiKeyId || !generateFormData.videoModel">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const props = defineProps({
  transitions: {
    type: Array,
    default: () => []
  },
  creating: {
    type: Boolean,
    default: false
  },
  generating: {
    type: Boolean,
    default: false
  },
  canCreate: {
    type: Boolean,
    default: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['create-transitions', 'generate-videos'])

const showCreateDialog = ref(false)
const showGenerateDialog = ref(false)
const createFormData = ref({
  apiKeyId: '',
  model: ''
})
const generateFormData = ref({
  apiKeyId: '',
  videoModel: 'veo_3_1-fast'
})
const textModelOptions = ref([])
const loadingTextModels = ref(false)

// 监听创建对话框的API Key变化
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
    } else {
      createFormData.value.model = ''
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

const handleCreateClick = () => {
  createFormData.value = {
    apiKeyId: props.apiKeys[0]?.id || '',
    model: ''
  }
  showCreateDialog.value = true
}

const handleCreateConfirm = () => {
  if (!createFormData.value.apiKeyId || !createFormData.value.model) {
    return
  }
  emit('create-transitions', createFormData.value.apiKeyId, createFormData.value.model)
  showCreateDialog.value = false
}

const handleGenerateClick = () => {
  generateFormData.value = {
    apiKeyId: props.apiKeys[0]?.id || '',
    videoModel: 'veo_3_1-fast'
  }
  showGenerateDialog.value = true
}

const handleGenerateConfirm = () => {
  if (!generateFormData.value.apiKeyId || !generateFormData.value.videoModel) {
    return
  }
  emit('generate-videos', generateFormData.value.apiKeyId, generateFormData.value.videoModel)
  showGenerateDialog.value = false
}
</script>

<style scoped>
.transition-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 10px;
}

.transition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.transition-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
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
}

.transition-number {
  font-weight: 600;
  color: #409eff;
}

.transition-content {
  margin-bottom: 12px;
}

.transition-prompt {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.transition-video {
  border-radius: 4px;
  overflow: hidden;
}

.transition-video video {
  width: 100%;
  height: auto;
  display: block;
}
</style>
