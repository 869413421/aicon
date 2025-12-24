<template>
  <div class="keyframe-panel">
    <div class="panel-header">
      <h3>关键帧生成</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="generating"
          :disabled="!canGenerate"
          @click="handleGenerateClick"
        >
          生成关键帧
        </el-button>
      </div>
    </div>

    <div class="keyframe-list">
      <el-empty v-if="shots.length === 0" description="暂无分镜数据" />
      
      <div v-else class="keyframe-grid">
        <div 
          v-for="shot in shots" 
          :key="shot.id"
          class="keyframe-card"
        >
          <div class="keyframe-header">
            <span class="shot-number">镜头 {{ shot.order_index }}</span>
            <el-tag v-if="shot.keyframe_url" type="success" size="small">已生成</el-tag>
            <el-tag v-else type="info" size="small">待生成</el-tag>
          </div>
          
          <div class="shot-description">
            <p>{{ shot.shot }}</p>
          </div>

          <div v-if="shot.keyframe_url" class="keyframe-image">
            <img :src="shot.keyframe_url" alt="关键帧" />
          </div>
          <div v-else class="keyframe-placeholder">
            <el-icon :size="40"><Picture /></el-icon>
            <p>待生成关键帧</p>
          </div>
        </div>
      </div>
    </div>

    <!-- API Key选择对话框 -->
    <el-dialog
      v-model="showDialog"
      title="生成关键帧"
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
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const props = defineProps({
  shots: {
    type: Array,
    default: () => []
  },
  generating: {
    type: Boolean,
    default: false
  },
  canGenerate: {
    type: Boolean,
    default: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['generate-keyframes'])

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
    const models = await api.get(`/api-keys/${newKeyId}/models?type=image`)
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

const handleGenerateClick = () => {
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
  emit('generate-keyframes', formData.value.apiKeyId, formData.value.model)
  showDialog.value = false
}
</script>

<style scoped>
.keyframe-panel {
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

.keyframe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.keyframe-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.keyframe-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.keyframe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.shot-number {
  font-weight: 600;
  color: #409eff;
}

.shot-description {
  margin-bottom: 12px;
}

.shot-description p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.keyframe-image {
  border-radius: 4px;
  overflow: hidden;
}

.keyframe-image img {
  width: 100%;
  height: auto;
  display: block;
}

.keyframe-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
}

.keyframe-placeholder p {
  margin: 8px 0 0 0;
  font-size: 13px;
}
</style>
