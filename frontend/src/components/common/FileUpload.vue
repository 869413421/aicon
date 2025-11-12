<template>
  <div class="file-upload">
    <div
      class="upload-area"
      :class="{
        'is-dragover': isDragOver,
        'is-uploading': isUploading,
        'is-disabled': disabled,
        'has-error': error,
      }"
      @click="handleClick"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        :multiple="multiple"
        :disabled="disabled || isUploading"
        @change="handleFileChange"
        style="display: none"
      />

      <!-- 上传状态显示 -->
      <div v-if="isUploading" class="upload-status">
        <el-icon class="is-loading" :size="48">
          <Loading />
        </el-icon>
        <p class="upload-text">正在上传...</p>
        <el-progress
          v-if="uploadProgress > 0"
          :percentage="uploadProgress"
          :status="uploadProgress === 100 ? 'success' : ''"
        />
      </div>

      <!-- 上传成功状态 -->
      <div v-else-if="uploadSuccess" class="upload-status upload-success">
        <el-icon :size="48" color="#67c23a">
          <Check />
        </el-icon>
        <p class="upload-text">上传成功</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="upload-status upload-error">
        <el-icon :size="48" color="#f56c6c">
          <Warning />
        </el-icon>
        <p class="upload-text">{{ error }}</p>
        <el-button type="text" @click="clearError">重试</el-button>
      </div>

      <!-- 默认状态 -->
      <div v-else class="upload-content">
        <el-icon :size="48" color="#c0c4cc">
          <UploadFilled />
        </el-icon>
        <p class="upload-text">
          {{ multiple ? '拖拽文件到此处或' : '拖拽文件到此处或' }}
          <el-button type="primary" link @click.stop="handleClick">
            点击上传
          </el-button>
        </p>
        <p class="upload-hint">
          支持 {{ accept }} 格式，文件大小不超过 {{ maxSize / 1024 / 1024 }}MB
        </p>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <h4 class="list-title">已选择的文件</h4>
      <div
        v-for="(file, index) in fileList"
        :key="index"
        class="file-item"
        :class="{ 'is-error': file.error }"
      >
        <div class="file-info">
          <el-icon class="file-icon">
            <Document />
          </el-icon>
          <div class="file-details">
            <p class="file-name" :title="file.name">{{ file.name }}</p>
            <p class="file-size">{{ formatFileSize(file.size) }}</p>
            <p v-if="file.error" class="file-error">{{ file.error }}</p>
          </div>
        </div>
        <div class="file-actions">
          <el-button
            v-if="file.uploading"
            type="text"
            size="small"
            :loading="true"
            disabled
          >
            上传中
          </el-button>
          <el-button
            v-else-if="file.success"
            type="text"
            size="small"
            icon="Check"
            disabled
          >
            已上传
          </el-button>
          <el-button
            v-else
            type="text"
            size="small"
            icon="Delete"
            @click="removeFile(index)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 上传历史 -->
    <div v-if="showHistory && uploadHistory.length > 0" class="upload-history">
      <h4 class="list-title">上传历史</h4>
      <div class="history-list">
        <div
          v-for="(item, index) in uploadHistory"
          :key="index"
          class="history-item"
        >
          <div class="history-info">
            <el-icon class="history-icon">
              <Document />
            </el-icon>
            <div class="history-details">
              <p class="history-name">{{ item.filename }}</p>
              <p class="history-time">{{ formatTime(item.uploadTime) }}</p>
            </div>
          </div>
          <div class="history-status">
            <el-tag
              :type="item.status === 'success' ? 'success' : 'danger'"
              size="small"
            >
              {{ item.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled,
  Loading,
  Check,
  Warning,
  Document,
  Delete,
} from '@element-plus/icons-vue'
import { uploadService } from '@/services/upload'

// Props定义
const props = defineProps({
  accept: {
    type: String,
    default: '.txt,.md,.docx,.epub',
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  maxSize: {
    type: Number,
    default: 50 * 1024 * 1024, // 50MB
  },
  maxFiles: {
    type: Number,
    default: 10,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  autoUpload: {
    type: Boolean,
    default: true,
  },
  showHistory: {
    type: Boolean,
    default: false,
  },
  projectData: {
    type: Object,
    default: () => ({}),
  },
})

// Emits定义
const emit = defineEmits([
  'file-selected',
  'upload-success',
  'upload-error',
  'upload-progress',
  'files-change',
])

// 响应式数据
const fileInput = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadSuccess = ref(false)
const error = ref('')
const fileList = ref([])
const uploadHistory = ref([])

// 计算属性
const selectedFilesCount = computed(() => fileList.value.length)

// 方法
const handleClick = () => {
  if (props.disabled || isUploading.value) return
  fileInput.value?.click()
}

const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  processFiles(files)
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event) => {
  event.preventDefault()
  isDragOver.value = false
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false

  if (props.disabled || isUploading.value) return

  const files = Array.from(event.dataTransfer.files)
  processFiles(files)
}

const processFiles = (files) => {
  if (!files.length) return

  // 验证文件数量
  if (!props.multiple && files.length > 1) {
    ElMessage.warning('只能选择一个文件')
    return
  }

  if (fileList.value.length + files.length > props.maxFiles) {
    ElMessage.warning(`最多只能选择 ${props.maxFiles} 个文件`)
    return
  }

  // 验证文件
  const validFiles = []
  const errors = []

  files.forEach((file) => {
    // 验证文件类型
    const fileExt = '.' + file.name.split('.').pop().toLowerCase()
    if (!props.accept.includes(fileExt)) {
      errors.push(`文件 ${file.name} 类型不支持`)
      return
    }

    // 验证文件大小
    if (file.size > props.maxSize) {
      errors.push(`文件 ${file.name} 大小超过限制`)
      return
    }

    validFiles.push(file)
  })

  if (errors.length > 0) {
    ElMessage.error(errors.join('; '))
    return
  }

  if (!validFiles.length) return

  // 添加到文件列表
  const newFiles = validFiles.map((file) => ({
    name: file.name,
    size: file.size,
    type: file.type,
    file: file,
    uploading: false,
    success: false,
    error: null,
    progress: 0,
  }))

  if (props.multiple) {
    fileList.value = [...fileList.value, ...newFiles]
  } else {
    fileList.value = newFiles
  }

  emit('file-selected', newFiles)
  emit('files-change', fileList.value)

  // 自动上传
  if (props.autoUpload) {
    uploadFiles()
  }
}

const uploadFiles = async () => {
  if (!fileList.value.length || isUploading.value) return

  isUploading.value = true
  error.value = ''
  uploadSuccess.value = false
  uploadProgress.value = 0

  try {
    const uploadPromises = fileList.value.map(async (fileItem, index) => {
      if (fileItem.success) return fileItem

      fileItem.uploading = true
      fileItem.error = null
      fileItem.progress = 0

      try {
        const formData = new FormData()
        formData.append('file', fileItem.file)
        formData.append('title', props.projectData.title || fileItem.name.replace(/\.[^/.]+$/, ''))

        if (props.projectData.description) {
          formData.append('description', props.projectData.description)
        }

        formData.append('auto_process', 'true')

        const response = await uploadService.uploadFile(formData, (progress) => {
          fileItem.progress = progress
          uploadProgress.value = Math.round(
            fileList.value.reduce((sum, f) => sum + f.progress, 0) / fileList.value.length
          )
          emit('upload-progress', uploadProgress.value)
        })

        fileItem.uploading = false
        fileItem.success = true
        fileItem.progress = 100

        emit('upload-success', {
          file: fileItem,
          response: response.data,
          index,
        })

        return fileItem

      } catch (err) {
        fileItem.uploading = false
        fileItem.error = err.message || '上传失败'

        emit('upload-error', {
          file: fileItem,
          error: err,
          index,
        })

        return fileItem
      }
    })

    await Promise.all(uploadPromises)

    // 检查是否有失败的上传
    const failedFiles = fileList.value.filter((f) => f.error)
    if (failedFiles.length > 0) {
      throw new Error(`${failedFiles.length} 个文件上传失败`)
    }

    uploadSuccess.value = true
    ElMessage.success('所有文件上传成功')

    // 添加到历史记录
    fileList.value.forEach((file) => {
      if (file.success) {
        uploadHistory.value.unshift({
          filename: file.name,
          uploadTime: new Date(),
          status: 'success',
        })
      }
    })

    // 限制历史记录数量
    if (uploadHistory.value.length > 20) {
      uploadHistory.value = uploadHistory.value.slice(0, 20)
    }

  } catch (err) {
    error.value = err.message
    ElMessage.error(error.value)

    emit('upload-error', {
      error: err,
      files: fileList.value,
    })
  } finally {
    isUploading.value = false
  }
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
  emit('files-change', fileList.value)

  if (fileList.value.length === 0) {
    clearError()
  }
}

const clearError = () => {
  error.value = ''
  uploadSuccess.value = false
  uploadProgress.value = 0
}

const clearFiles = () => {
  fileList.value = []
  clearError()
  emit('files-change', [])
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (time) => {
  const now = new Date()
  const diff = now - new Date(time)
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}天前`
  if (hours > 0) return `${hours}小时前`
  if (minutes > 0) return `${minutes}分钟前`
  return '刚刚'
}

// 暴露给父组件的方法
defineExpose({
  uploadFiles,
  clearFiles,
  clearError,
  getFileList: () => fileList.value,
})

// 监听器
watch(fileList, (newList) => {
  if (newList.length === 0) {
    uploadSuccess.value = false
    error.value = ''
    uploadProgress.value = 0
  }
})
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.upload-area:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.upload-area.is-dragover {
  border-color: #409eff;
  background-color: #f0f9ff;
  transform: scale(1.02);
}

.upload-area.is-uploading {
  border-color: #e6a23c;
  background-color: #fdf6ec;
  cursor: not-allowed;
}

.upload-area.is-disabled {
  border-color: #e4e7ed;
  background-color: #f5f7fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-area.has-error {
  border-color: #f56c6c;
  background-color: #fef0f0;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-status.upload-success {
  color: #67c23a;
}

.upload-status.upload-error {
  color: #f56c6c;
}

.upload-text {
  margin: 0;
  font-size: 16px;
  color: #606266;
  line-height: 1.5;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.file-list {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.list-title {
  margin: 0;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item.is-error {
  background-color: #fef0f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  color: #909399;
  font-size: 20px;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.file-error {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #f56c6c;
}

.file-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.upload-history {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.history-item:last-child {
  border-bottom: none;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.history-icon {
  color: #909399;
  font-size: 16px;
}

.history-details {
  flex: 1;
  min-width: 0;
}

.history-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.history-status {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .upload-area {
    padding: 30px 15px;
    min-height: 150px;
  }

  .file-item,
  .history-item {
    padding: 10px 12px;
  }

  .file-actions {
    flex-direction: column;
    gap: 4px;
  }
}
</style>