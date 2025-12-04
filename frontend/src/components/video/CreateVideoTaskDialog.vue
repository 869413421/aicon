<template>
  <el-dialog
    title="新建视频生成任务"
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      v-loading="loading"
    >
      <el-form-item label="选择章节" prop="chapter_id">
        <el-select
          v-model="form.chapter_id"
          placeholder="请选择已准备好素材的章节"
          filterable
          remote
          :remote-method="searchChapters"
          :loading="chapterLoading"
          style="width: 100%"
        >
          <el-option
            v-for="item in chapters"
            :key="item.id"
            :label="item.title"
            :value="item.id"
          >
            <span style="float: left">{{ item.title }}</span>
            <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
              {{ item.project_title }}
            </span>
          </el-option>
        </el-select>
        <div class="form-tip">仅显示状态为"素材已准备"的章节</div>
      </el-form-item>

      <el-divider content-position="left">生成设置</el-divider>

      <el-form-item label="分辨率" prop="gen_setting.resolution">
        <el-select v-model="form.gen_setting.resolution" style="width: 100%">
          <el-option label="竖屏 9:16 (1080x1920)" value="1080x1920" />
          <el-option label="横屏 16:9 (1920x1080)" value="1920x1080" />
          <el-option label="方形 1:1 (1080x1080)" value="1080x1080" />
        </el-select>
      </el-form-item>

      <el-form-item label="帧率" prop="gen_setting.fps">
        <el-radio-group v-model="form.gen_setting.fps">
          <el-radio-button :label="24">24 FPS</el-radio-button>
          <el-radio-button :label="30">30 FPS</el-radio-button>
          <el-radio-button :label="60">60 FPS</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="字幕纠错" prop="api_key_id">
        <el-select
          v-model="form.api_key_id"
          placeholder="选择API密钥以启用LLM字幕纠错"
          clearable
          style="width: 100%"
        >
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="key.name"
            :value="key.id"
          >
            <span>{{ key.name }}</span>
            <span style="float: right; color: var(--el-text-color-secondary); font-size: 12px">
              {{ key.provider }}
            </span>
          </el-option>
        </el-select>
        <div class="form-tip">
          启用后将使用LLM自动修正Whisper生成的字幕错别字。
          <span v-if="!form.api_key_id" class="text-warning">未选择API密钥，将使用原始字幕。</span>
        </div>
      </el-form-item>

      <el-form-item 
        v-if="form.api_key_id" 
        label="LLM模型" 
        prop="gen_setting.llm_model"
      >
        <el-input v-model="form.gen_setting.llm_model" placeholder="例如: gpt-4o-mini, deepseek-chat" />
      </el-form-item>

      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="高级设置" name="advanced">
          <el-divider content-position="left">字幕样式</el-divider>
          <el-row :gutter="15">
            <el-col :span="12">
              <el-form-item label="字体大小" prop="gen_setting.subtitle_style.font_size">
                <el-input-number 
                  v-model="form.gen_setting.subtitle_style.font_size" 
                  :min="20" 
                  :max="100" 
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="位置" prop="gen_setting.subtitle_style.position">
                <el-select v-model="form.gen_setting.subtitle_style.position" style="width: 100%">
                  <el-option label="底部" value="bottom" />
                  <el-option label="顶部" value="top" />
                  <el-option label="中间" value="center" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="镜头移动">
            <el-switch 
              v-model="enableZoom" 
              active-text="启用推拉效果"
              @change="handleZoomChange"
            />
          </el-form-item>
          
          
          <el-form-item label="缩放速度" v-if="enableZoom">
            <el-slider 
              v-model="zoomSpeedDisplay" 
              :min="1" 
              :max="10" 
              :format-tooltip="val => `${val/10000} / frame`"
            />
          </el-form-item>

          <el-divider content-position="left">背景音乐</el-divider>
          <el-form-item label="BGM选择">
            <el-select 
              v-model="form.bgm_id" 
              placeholder="选择背景音乐（可选）"
              clearable
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="bgm in bgmList"
                :key="bgm.id"
                :label="`${bgm.name} (${formatDuration(bgm.duration)})`"
                :value="bgm.id"
              />
            </el-select>
            <span class="form-tip">为视频添加背景音乐，将与原音频混合</span>
          </el-form-item>

          <el-divider content-position="left">视频速度</el-divider>
          <el-form-item label="播放速度">
            <el-slider 
              v-model="form.gen_setting.video_speed" 
              :min="0.5" 
              :max="2.0" 
              :step="0.1"
              :marks="{ 0.5: '0.5x', 1.0: '1.0x', 1.5: '1.5x', 2.0: '2.0x' }"
              :format-tooltip="val => `${val}x`"
              style="margin: 0 12px"
            />
            <span class="form-tip">调整视频播放速度，音调会自动保持</span>
          </el-form-item>
        </el-collapse-item>
      </el-collapse>

    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          开始生成
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { useVideoTasks } from '@/composables/useVideoTasks'
import { chaptersService } from '@/services/chapters'
import { apiKeysService } from '@/services/apiKeys'
import bgmService from '@/services/bgm'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'success'])

const { createTask } = useVideoTasks()

// 状态
const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const chapterLoading = ref(false)
const chapters = ref([])
const apiKeys = ref([])
const bgmList = ref([])
const activeCollapse = ref([])
const enableZoom = ref(true)
const zoomSpeedDisplay = ref(5) // 对应 0.0005

const form = reactive({
  chapter_id: '',
  api_key_id: '',
  bgm_id: '',
  gen_setting: {
    resolution: '1080x1920',
    fps: 30,
    video_codec: 'libx264',
    audio_codec: 'aac',
    audio_bitrate: '192k',
    zoom_speed: 0.0005,
    video_speed: 1.0,
    llm_model: 'gpt-4o-mini',
    subtitle_style: {
      font: 'Arial',
      font_size: 70,
      color: 'white',
      position: 'bottom'
    }
  }
})

const rules = {
  chapter_id: [{ required: true, message: '请选择章节', trigger: 'change' }],
  'gen_setting.resolution': [{ required: true, message: '请选择分辨率', trigger: 'change' }],
  'gen_setting.fps': [{ required: true, message: '请选择帧率', trigger: 'change' }]
}

// 监听器
watch(() => props.modelValue, (val) => {
  if (val) {
    loadData()
  } else {
    resetForm()
  }
})

watch(zoomSpeedDisplay, (val) => {
  form.gen_setting.zoom_speed = val / 10000
})

// 方法
const loadData = async () => {
  loading.value = true
  try {
    // 加载API密钥
    const keysRes = await apiKeysService.getAPIKeys({ size: 100, status: 'active' })
    apiKeys.value = keysRes.api_keys || []
    
    // 加载BGM列表
    const bgmRes = await bgmService.getBGMs({ size: 100 })
    bgmList.value = bgmRes.bgms || []
    
    // 初始加载章节（materials_prepared状态）
    await searchChapters('')
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const searchChapters = async (query) => {
  chapterLoading.value = true
  try {
    const res = await chaptersService.getChapters(null, {
      search: query,
      chapter_status: 'materials_prepared', // 只显示素材准备好的章节
      size: 50
    })
    chapters.value = res.chapters || []
  } catch (error) {
    console.error('搜索章节失败:', error)
  } finally {
    chapterLoading.value = false
  }
}

const handleZoomChange = (val) => {
  if (val) {
    form.gen_setting.zoom_speed = zoomSpeedDisplay.value / 10000
  } else {
    form.gen_setting.zoom_speed = 0
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await createTask({
          chapter_id: form.chapter_id,
          api_key_id: form.api_key_id || null,
          bgm_id: form.bgm_id || null,
          gen_setting: form.gen_setting
        })
        emit('success')
        emit('update:modelValue', false)
      } catch (error) {
        // 错误已在composable中处理
      } finally {
        submitting.value = false
      }
    }
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.chapter_id = ''
  form.api_key_id = ''
  // 重置为默认值
  form.gen_setting = {
    resolution: '1080x1920',
    fps: 30,
    video_codec: 'libx264',
    audio_codec: 'aac',
    audio_bitrate: '192k',
    zoom_speed: 0.0005,
    llm_model: 'gpt-4o-mini',
    subtitle_style: {
      font: 'Arial',
      font_size: 70,
      color: 'white',
      position: 'bottom'
    }
  }
  enableZoom.value = true
  zoomSpeedDisplay.value = 5
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-top: 4px;
}

.text-warning {
  color: var(--warning-color);
}
</style>
