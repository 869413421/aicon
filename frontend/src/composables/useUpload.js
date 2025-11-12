/**
 * 文件上传组合式API
 * 提供文件上传的通用逻辑和状态管理
 */

import { ref, reactive, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadAPI, fileValidator, uploadManager } from '@/services/upload'
import { useProjectsStore } from '@/stores/projects'

export function useUpload(options = {}) {
  const {
    maxFileSize = 100 * 1024 * 1024, // 100MB
    allowedTypes = ['.txt', '.md', '.docx', '.epub'],
    autoUpload = true,
    multiple = false,
    onProgress = null,
    onSuccess = null,
    onError = null,
    onComplete = null
  } = options

  // Store实例
  const projectsStore = useProjectsStore()

  // 状态定义
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const uploadError = ref(null)
  const selectedFiles = ref([])
  const uploadResults = ref([])

  // 上传任务管理
  const uploadTasks = reactive(new Map())

  // 计算属性
  const hasSelectedFiles = computed(() => selectedFiles.value.length > 0)
  const totalProgress = computed(() => {
    if (uploadTasks.size === 0) return 0
    let totalProgress = 0
    uploadTasks.forEach(task => {
      totalProgress += task.progress
    })
    return Math.round(totalProgress / uploadTasks.size)
  })
  const allCompleted = computed(() => {
    if (uploadTasks.size === 0) return false
    return Array.from(uploadTasks.values()).every(task => task.status === 'completed')
  })
  const hasErrors = computed(() => {
    return Array.from(uploadTasks.values()).some(task => task.status === 'failed')
  })

  // 方法
  /**
   * 验证文件
   * @param {File} file - 文件对象
   * @returns {Object} 验证结果
   */
  const validateFile = (file) => {
    const result = {
      valid: true,
      errors: []
    }

    // 检查文件类型
    if (!fileValidator.isValidFileType(file, allowedTypes)) {
      result.valid = false
      result.errors.push(`不支持的文件类型，仅支持: ${allowedTypes.join(', ')}`)
    }

    // 检查文件大小
    if (!fileValidator.isValidFileSize(file, maxFileSize)) {
      result.valid = false
      result.errors.push(`文件大小超过限制，最大允许: ${fileValidator.formatFileSize(maxFileSize)}`)
    }

    // 检查文件名
    if (!file.name || file.name.trim() === '') {
      result.valid = false
      result.errors.push('文件名不能为空')
    }

    return result
  }

  /**
   * 选择文件
   * @param {FileList} files - 文件列表
   */
  const selectFiles = (files) => {
    const fileArray = Array.from(files)

    // 如果不支持多文件，只取第一个
    if (!multiple && fileArray.length > 1) {
      fileArray.splice(1)
    }

    // 验证文件
    const validFiles = []
    const invalidFiles = []

    fileArray.forEach(file => {
      const validation = validateFile(file)
      if (validation.valid) {
        validFiles.push(file)
      } else {
        invalidFiles.push({ file, errors: validation.errors })
      }
    })

    // 显示错误信息
    if (invalidFiles.length > 0) {
      const errorMessages = invalidFiles.map(({ file, errors }) =>
        `${file.name}: ${errors.join(', ')}`
      )
      ElMessage.error(`文件验证失败:\n${errorMessages.join('\n')}`)
    }

    // 更新选中的文件
    if (multiple) {
      selectedFiles.value = [...selectedFiles.value, ...validFiles]
    } else {
      selectedFiles.value = validFiles
    }

    // 清除之前的错误
    uploadError.value = null

    // 自动上传
    if (autoUpload && validFiles.length > 0) {
      startUpload(validFiles)
    }

    return {
      validFiles,
      invalidFiles
    }
  }

  /**
   * 移除选中的文件
   * @param {File} file - 要移除的文件
   */
  const removeFile = (file) => {
    const index = selectedFiles.value.findIndex(f => f === file)
    if (index !== -1) {
      selectedFiles.value.splice(index, 1)
    }
  }

  /**
   * 清空选中的文件
   */
  const clearFiles = () => {
    selectedFiles.value = []
    uploadError.value = null
  }

  /**
   * 开始上传
   * @param {Array} files - 要上传的文件列表
   * @param {Object} options - 上传选项
   */
  const startUpload = async (files, uploadOptions = {}) => {
    if (!files || files.length === 0) {
      ElMessage.warning('请先选择文件')
      return
    }

    uploading.value = true
    uploadError.value = null
    uploadResults.value = []

    try {
      for (const file of files) {
        await uploadSingleFile(file, uploadOptions)
      }

      // 上传完成
      if (onComplete) {
        onComplete(uploadResults.value)
      }

      ElMessage.success('文件上传完成')

    } catch (error) {
      console.error('批量上传失败:', error)
      uploadError.value = error.message || '上传失败'

      if (onError) {
        onError(error)
      }
    } finally {
      uploading.value = false
    }
  }

  /**
   * 上传单个文件
   * @param {File} file - 文件对象
   * @param {Object} options - 上传选项
   */
  const uploadSingleFile = async (file, options = {}) => {
    const taskId = Date.now().toString() + Math.random().toString(36).substr(2, 9)

    // 创建上传任务
    const task = {
      id: taskId,
      file,
      status: 'pending',
      progress: 0,
      error: null,
      result: null,
      startTime: new Date(),
      ...options
    }

    uploadTasks.set(taskId, task)

    try {
      // 验证文件完整性
      const isValid = await fileValidator.validateFileIntegrity(file)
      if (!isValid) {
        throw new Error('文件完整性验证失败')
      }

      // 准备表单数据
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', options.title || file.name.replace(/\.[^/.]+$/, ''))
      formData.append('description', options.description || '')
      formData.append('auto_process', options.autoProcess !== false)

      // 开始上传
      task.status = 'uploading'

      const result = await uploadAPI.uploadFile({
        formData,
        onProgress: (progress) => {
          task.progress = progress
          uploadProgress.value = totalProgress.value

          if (onProgress) {
            onProgress(progress, task)
          }
        }
      })

      // 上传成功
      task.status = 'completed'
      task.progress = 100
      task.result = result
      task.endTime = new Date()

      uploadResults.value.push(result)

      // 更新项目列表
      if (result.success && result.data?.project) {
        projectsStore.projects.unshift(result.data.project)
      }

      if (onSuccess) {
        onSuccess(result, task)
      }

      return result

    } catch (error) {
      // 上传失败
      task.status = 'failed'
      task.error = error.message || '上传失败'
      task.endTime = new Date()

      uploadError.value = task.error

      if (onError) {
        onError(error, task)
      }

      throw error

    } finally {
      // 清理完成的任务（延迟清理）
      setTimeout(() => {
        uploadTasks.delete(taskId)
      }, 5000)
    }
  }

  /**
   * 取消上传
   * @param {string} taskId - 任务ID（可选）
   */
  const cancelUpload = (taskId) => {
    if (taskId) {
      const task = uploadTasks.get(taskId)
      if (task && (task.status === 'pending' || task.status === 'uploading')) {
        task.status = 'cancelled'
        uploadTasks.delete(taskId)
      }
    } else {
      // 取消所有上传任务
      uploadTasks.forEach((task, id) => {
        if (task.status === 'pending' || task.status === 'uploading') {
          task.status = 'cancelled'
        }
      })
      uploadTasks.clear()
      uploading.value = false
    }
  }

  /**
   * 重试上传
   * @param {string} taskId - 任务ID
   */
  const retryUpload = async (taskId) => {
    const task = uploadTasks.get(taskId)
    if (task && task.status === 'failed') {
      // 重置任务状态
      task.status = 'pending'
      task.progress = 0
      task.error = null
      task.result = null

      try {
        await uploadSingleFile(task.file, task)
      } catch (error) {
        console.error('重试上传失败:', error)
      }
    }
  }

  /**
   * 重试所有失败的上传
   */
  const retryAllFailed = async () => {
    const failedTasks = Array.from(uploadTasks.values()).filter(
      task => task.status === 'failed'
    )

    for (const task of failedTasks) {
      await retryUpload(task.id)
    }
  }

  /**
   * 清理已完成的任务
   */
  const cleanupTasks = () => {
    const now = Date.now()
    const completedTasks = []

    uploadTasks.forEach((task, id) => {
      const age = now - new Date(task.endTime || task.startTime).getTime()
      if (age > 5 * 60 * 1000) { // 5分钟前的任务
        completedTasks.push(id)
      }
    })

    completedTasks.forEach(id => uploadTasks.delete(id))
  }

  /**
   * 获取上传统计
   */
  const getUploadStats = () => {
    const tasks = Array.from(uploadTasks.values())
    return {
      total: tasks.length,
      pending: tasks.filter(t => t.status === 'pending').length,
      uploading: tasks.filter(t => t.status === 'uploading').length,
      completed: tasks.filter(t => t.status === 'completed').length,
      failed: tasks.filter(t => t.status === 'failed').length,
      cancelled: tasks.filter(t => t.status === 'cancelled').length,
      totalSize: tasks.reduce((sum, task) => sum + (task.file?.size || 0), 0),
      uploadedSize: tasks
        .filter(t => t.status === 'completed')
        .reduce((sum, task) => sum + (task.file?.size || 0), 0)
    }
  }

  // 监听上传管理器状态变化
  const handleUploadManagerChange = (uploads) => {
    // 同步外部上传管理器的状态
    uploads.forEach(upload => {
      if (!uploadTasks.has(upload.id)) {
        uploadTasks.set(upload.id, upload)
      }
    })
  }

  // 注册监听器
  uploadManager.addListener(handleUploadManagerChange)

  // 组件卸载时清理
  onUnmounted(() => {
    uploadManager.removeListener(handleUploadManagerChange)
    cleanupTasks()
  })

  return {
    // 状态
    uploading,
    uploadProgress,
    uploadError,
    selectedFiles,
    uploadResults,
    uploadTasks,

    // 计算属性
    hasSelectedFiles,
    totalProgress,
    allCompleted,
    hasErrors,

    // 方法
    validateFile,
    selectFiles,
    removeFile,
    clearFiles,
    startUpload,
    uploadSingleFile,
    cancelUpload,
    retryUpload,
    retryAllFailed,
    cleanupTasks,
    getUploadStats,

    // 工具函数
    formatFileSize: fileValidator.formatFileSize,
    getFileTypeDescription: fileValidator.getFileTypeDescription
  }
}

/**
 * 创建项目上传的组合式API
 * 专门用于创建项目的文件上传
 */
export function useProjectUpload(options = {}) {
  const upload = useUpload({
    maxFileSize: 100 * 1024 * 1024,
    allowedTypes: ['.txt', '.md', '.docx', '.epub'],
    autoUpload: false,
    multiple: false,
    ...options
  })

  const projectsStore = useProjectsStore()

  /**
   * 上传文件并创建项目
   * @param {Object} projectData - 项目数据
   */
  const uploadAndCreateProject = async (projectData) => {
    if (!upload.selectedFiles.value.length) {
      ElMessage.warning('请先选择文件')
      return
    }

    const file = upload.selectedFiles.value[0]

    try {
      upload.uploading.value = true
      upload.uploadError.value = null

      // 添加上传任务到store
      const taskId = projectsStore.addUploadTask({
        fileName: file.name,
        fileSize: file.size,
        fileType: fileValidator.getFileTypeDescription(file.name),
        projectTitle: projectData.title || file.name.replace(/\.[^/.]+$/, '')
      })

      // 准备表单数据
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', projectData.title || file.name.replace(/\.[^/.]+$/, ''))
      formData.append('description', projectData.description || '')
      formData.append('auto_process', projectData.autoProcess !== false)

      // 上传文件
      const result = await uploadAPI.uploadFile({
        formData,
        onProgress: (progress) => {
          upload.uploadProgress.value = progress
          projectsStore.updateUploadTask(taskId, { progress })
        }
      })

      // 上传成功
      if (result.success && result.data?.project) {
        projectsStore.completeUploadTask(taskId, result.data.project)
        projectsStore.projects.unshift(result.data.project)

        ElMessage.success('项目创建成功')
        return result.data.project
      } else {
        throw new Error(result.message || '创建项目失败')
      }

    } catch (error) {
      upload.uploadError.value = error.message || '上传失败'
      ElMessage.error(upload.uploadError.value)
      throw error
    } finally {
      upload.uploading.value = false
    }
  }

  return {
    ...upload,
    uploadAndCreateProject
  }
}

export default useUpload