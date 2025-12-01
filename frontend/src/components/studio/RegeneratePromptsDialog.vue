<template>
  <el-dialog
    v-model="dialogVisible"
    title="重新生成提示词"
    width="500px"
  >
    <el-form :inline="false" class="dialog-form">
      <el-form-item label="API Key" style="width: 100%">
        <el-select v-model="selectedApiKey" placeholder="选择API Key" style="width: 100%">
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="`${key.name} (${key.provider})`"
            :value="key.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="模型" style="width: 100%">
        <el-select 
          v-model="selectedModel" 
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
      
      <el-form-item label="风格" style="width: 100%">
        <el-select v-model="selectedStyle" placeholder="选择风格" style="width: 100%">
          <el-option label="电影质感 (Cinematic)" value="cinematic" />
          <el-option label="二次元 (Anime)" value="anime" />
          <el-option label="插画 (Illustration)" value="illustration" />
          <el-option label="水墨 (Ink)" value="ink" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="系统提示词" style="width: 100%">
        <el-input
          v-model="customPrompt"
          type="textarea"
          :rows="6"
          placeholder="输入自定义系统提示词，或选择风格后自动填充默认提示词"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="regenerating" @click="handleRegenerate">
          重新生成
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  sentenceIds: {
    type: Array,
    required: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'regenerate-success'])

const dialogVisible = ref(props.visible)
const selectedApiKey = ref('')
const selectedStyle = ref('cinematic')
const selectedModel = ref('')
const modelOptions = ref([])
const loadingModels = ref(false)
const customPrompt = ref('')
const regenerating = ref(false)

// 风格对应的默认提示词
const STYLE_PROMPTS = {
  cinematic: `你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的提示词。

请遵循以下规则：
1. 输出必须是纯文本，不要包含markdown语法或解释性内容。
2. 不要加入前缀/后缀，例如"Here is the prompt:"。
3. 提示词结构建议为：Subject, Action, Background, Lighting, Style, Quality。
4. 正确表达句子的视觉元素、情绪与意境。
5. 如果句子没有明确画面（如心理描写），请生成符合氛围的意象画面。

风格要求：Cinematic lighting, 8k resolution, photorealistic, movie still, detailed texture, dramatic atmosphere.`,
  anime: `你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的提示词。

请遵循以下规则：
1. 输出必须是纯文本，不要包含markdown语法或解释性内容。
2. 不要加入前缀/后缀，例如"Here is the prompt:"。
3. 提示词结构建议为：Subject, Action, Background, Lighting, Style, Quality。
4. 正确表达句子的视觉元素、情绪与意境。
5. 如果句子没有明确画面（如心理描写），请生成符合氛围的意象画面。

风格要求：Anime style, Makoto Shinkai style, vibrant colors, detailed background, high quality.`,
  illustration: `你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的提示词。

请遵循以下规则：
1. 输出必须是纯文本，不要包含markdown语法或解释性内容。
2. 不要加入前缀/后缀，例如"Here is the prompt:"。
3. 提示词结构建议为：Subject, Action, Background, Lighting, Style, Quality。
4. 正确表达句子的视觉元素、情绪与意境。
5. 如果句子没有明确画面（如心理描写），请生成符合氛围的意象画面。

风格要求：Digital illustration, artstation, concept art, fantasy style, detailed.`,
  ink: `你是一个专业的AI绘画提示词生成专家(AI Director)。
你的任务是将中文小说句子转换为高质量的提示词。

请遵循以下规则：
1. 输出必须是纯文本，不要包含markdown语法或解释性内容。
2. 不要加入前缀/后缀，例如"Here is the prompt:"。
3. 提示词结构建议为：Subject, Action, Background, Lighting, Style, Quality。
4. 正确表达句子的视觉元素、情绪与意境。
5. 如果句子没有明确画面（如心理描写），请生成符合氛围的意象画面。

风格要求：Chinese ink painting style, watercolor, traditional art, artistic, abstract.`
}

// 监听visible prop变化，更新dialogVisible
watch(() => props.visible, (newValue) => {
  dialogVisible.value = newValue
  // 对话框打开时，如果没有自定义提示词，设置默认提示词
  if (newValue && !customPrompt.value) {
    customPrompt.value = STYLE_PROMPTS[selectedStyle.value] || STYLE_PROMPTS.cinematic
  }
})

// 监听风格变化，更新默认提示词
watch(selectedStyle, (newStyle) => {
  customPrompt.value = STYLE_PROMPTS[newStyle] || STYLE_PROMPTS.cinematic
})

// 监听selectedApiKey变化，获取可用模型
watch(selectedApiKey, async (newKeyId) => {
  if (!newKeyId) {
    modelOptions.value = []
    selectedModel.value = ''
    return
  }
  
  loadingModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models`)
    modelOptions.value = models || []
    // 如果有模型，自动选择第一个
    if (modelOptions.value.length > 0) {
      selectedModel.value = modelOptions.value[0]
    } else {
      selectedModel.value = ''
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    modelOptions.value = []
    selectedModel.value = ''
  } finally {
    loadingModels.value = false
  }
})

// 更新visible状态并通知父组件
const updateDialogVisible = (newValue) => {
  dialogVisible.value = newValue
  emit('update:visible', newValue)
}

// 处理取消
const handleCancel = () => {
  updateDialogVisible(false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedApiKey.value = ''
  selectedStyle.value = 'cinematic'
  selectedModel.value = ''
  modelOptions.value = []
  customPrompt.value = ''
}

// 处理重新生成
const handleRegenerate = async () => {
  if (!selectedApiKey.value || props.sentenceIds.length === 0) {
    ElMessage.warning('请选择API Key和要重新生成的句子')
    return
  }
  
  regenerating.value = true
  try {
    const response = await api.post('/prompt/generate-prompts-ids', {
      api_key_id: selectedApiKey.value,
      sentence_ids: props.sentenceIds,
      style: selectedStyle.value,
      model: selectedModel.value || null,
      custom_prompt: customPrompt.value || null
    })
    
    if (response.success) {
      ElMessage.success(response.message)
      updateDialogVisible(false)
      emit('regenerate-success', response.task_id)
      resetForm()
    }
  } catch (error) {
    console.error('重新生成失败', error)
    ElMessage.error('重新生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    regenerating.value = false
  }
}
</script>

<style scoped>
.dialog-form {
  margin-bottom: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>