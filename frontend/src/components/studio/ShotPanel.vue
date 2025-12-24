<template>
  <div class="shot-panel">
    <div class="panel-header">
      <h3>分镜列表</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="extracting"
          :disabled="!canExtract"
          @click="handleExtractClick"
        >
          提取分镜
        </el-button>
      </div>
    </div>

    <div class="shot-list">
      <el-empty v-if="shots.length === 0" description="暂无分镜，请先提取分镜" />
      
      <div v-else class="shot-grid">
        <div 
          v-for="shot in shots" 
          :key="shot.id"
          class="shot-card"
        >
          <div class="shot-header">
            <span class="shot-number">镜头 {{ shot.order_index }}</span>
            <el-tag v-if="shot.keyframe_url" type="success" size="small">已生成关键帧</el-tag>
          </div>
          
          <div class="shot-content">
            <p class="shot-description">{{ shot.shot }}</p>
            <p v-if="shot.dialogue" class="shot-dialogue">💬 {{ shot.dialogue }}</p>
          </div>

          <div v-if="shot.keyframe_url" class="shot-keyframe">
            <img :src="shot.keyframe_url" alt="关键帧" />
          </div>
        </div>
      </div>
    </div>

    <!-- API Key选择对话框 -->
    <el-dialog
      v-model="showDialog"
      title="提取分镜"
      width="500px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="API Key">
          <el-select v-model="formData.apiKeyId" placeholder="请选择API Key" style="width: 100%">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="`${key.name} (${key.provider})`"
              :value="key.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select 
            v-model="formData.model" 
            placeholder="选择模型" 
            style="width: 100%"
            :loading="loadingModels"
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="model in modelOptions"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleDialogConfirm" :disabled="!formData.apiKeyId || !formData.model">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const props = defineProps({
  shots: {
    type: Array,
    default: () => []
  },
  extracting: {
    type: Boolean,
    default: false
  },
  canExtract: {
    type: Boolean,
    default: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['extract-shots'])

const showDialog = ref(false)
const formData = ref({
  apiKeyId: '',
  model: ''
})
const modelOptions = ref([])
const loadingModels = ref(false)

// 监听API Key变化，自动加载模型列表
watch(() => formData.value.apiKeyId, async (newKeyId) => {
  if (!newKeyId) {
    modelOptions.value = []
    formData.value.model = ''
    return
  }
  
  loadingModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=text`)
    modelOptions.value = models || []
    if (modelOptions.value.length > 0) {
      formData.value.model = modelOptions.value[0]
    } else {
      formData.value.model = ''
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    modelOptions.value = []
    formData.value.model = ''
  } finally {
    loadingModels.value = false
  }
})

const handleExtractClick = () => {
  formData.value = {
    apiKeyId: props.apiKeys[0]?.id || '',
    model: ''
  }
  showDialog.value = true
}

const handleDialogConfirm = () => {
  if (!formData.value.apiKeyId || !formData.value.model) {
    return
  }
  emit('extract-shots', formData.value.apiKeyId, formData.value.model)
  showDialog.value = false
}
</script>

<style scoped>
.shot-panel {
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

.shot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.shot-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.shot-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.shot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.shot-number {
  font-weight: 600;
  color: #409eff;
}

.shot-content {
  margin-bottom: 12px;
}

.shot-description {
  margin: 0 0 8px 0;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.shot-dialogue {
  margin: 0;
  font-size: 13px;
  color: #909399;
  font-style: italic;
}

.shot-keyframe {
  margin-top: 12px;
  border-radius: 4px;
  overflow: hidden;
}

.shot-keyframe img {
  width: 100%;
  height: auto;
  display: block;
}
</style>
