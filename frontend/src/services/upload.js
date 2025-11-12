import { get, post, del, upload } from './api'

/**
 * 文件管理服务 - 职责分离后的纯文件操作
 */
export const fileService = {
  /**
   * 纯文件上传，返回文件ID
   * @param {FormData} formData - 包含文件的表单数据
   * @param {Function} onProgress - 进度回调函数
   * @returns {Promise} 上传结果，包含file_id
   */
  async uploadFile(formData, onProgress) {
    return await upload('/files/upload', formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percentCompleted)
        }
      }
    })
  },

  /**
   * 删除文件
   * @param {string} fileId - 文件ID
   * @returns {Promise} 删除结果
   */
  async deleteFile(fileId) {
    return await del(`/files/${fileId}`)
  },

  /**
   * 获取文件信息
   * @param {string} fileId - 文件ID
   * @returns {Promise} 文件信息
   */
  async getFileInfo(fileId) {
    return await get(`/files/${fileId}`)
  },

  /**
   * 获取文件下载URL
   * @param {string} fileId - 文件ID
   * @returns {Promise} 下载URL信息
   */
  async getDownloadUrl(fileId) {
    return await get(`/files/${fileId}/download`)
  }
}

/**
 * 项目服务 - 专门处理项目CRUD操作
 */
export const projectService = {
  /**
   * 创建空项目
   * @param {Object} projectData - 项目数据
   * @returns {Promise} 创建结果
   */
  async createProject(projectData) {
    return await post('/projects/', projectData)
  },

  /**
   * 通过文件ID创建项目
   * @param {Object} projectData - 包含file_id的项目数据
   * @returns {Promise} 创建结果
   */
  async createProjectWithFile(projectData) {
    return await post('/projects/with-file', projectData)
  },

  /**
   * 获取项目列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 项目列表
   */
  async getProjects(params) {
    return await get('/projects/', { params })
  },

  /**
   * 获取项目详情
   * @param {string} projectId - 项目ID
   * @returns {Promise} 项目详情
   */
  async getProject(projectId) {
    return await get(`/projects/${projectId}`)
  },

  /**
   * 更新项目
   * @param {string} projectId - 项目ID
   * @param {Object} projectData - 更新数据
   * @returns {Promise} 更新结果
   */
  async updateProject(projectId, projectData) {
    return await post(`/projects/${projectId}`, projectData)
  },

  /**
   * 删除项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 删除结果
   */
  async deleteProject(projectId) {
    return await del(`/projects/${projectId}`)
  }
}

/**
 * 兼容性包装器 - 为了保持向后兼容
 * @deprecated 建议使用 fileService 和 projectService
 */
export const uploadService = {
  /**
   * 上传文件（兼容性方法）
   * @param {Object} data - 上传数据
   * @returns {Promise} 上传结果
   */
  async uploadFile(data) {
    const { formData, onProgress } = data
    return await fileService.uploadFile(formData, onProgress)
  },

  /**
   * 从URL上传文件
   * @param {Object} data - 上传数据
   * @param {string} data.fileUrl - 文件URL
   * @param {string} data.title - 项目标题
   * @param {string} data.description - 项目描述
   * @param {boolean} data.autoProcess - 是否自动处理
   * @returns {Promise} 上传结果
   */
  async uploadFromUrl(data) {
    const formData = new FormData()
    formData.append('file_url', data.fileUrl)
    formData.append('title', data.title)
    formData.append('description', data.description || '')
    formData.append('auto_process', data.autoProcess !== false)

    return await post('/upload/upload-url', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取预签名上传URL
   * @param {Object} params - 参数
   * @param {string} params.filename - 文件名
   * @param {string} params.fileType - 文件类型
   * @param {number} params.expiresIn - 过期时间（秒）
   * @returns {Promise} 预签名URL信息
   */
  async getPresignedUrl(params) {
    return await get('/upload/presigned-url', { params })
  },

  /**
   * 删除文件
   * @param {string} objectKey - 文件对象键
   * @returns {Promise} 删除结果
   */
  async deleteFile(objectKey) {
    return await del(`/upload/file/${encodeURIComponent(objectKey)}`)
  },

  /**
   * 获取文件信息
   * @param {string} objectKey - 文件对象键
   * @returns {Promise} 文件信息
   */
  async getFileInfo(objectKey) {
    return await get(`/upload/file-info/${encodeURIComponent(objectKey)}`)
  },

  /**
   * 重新处理项目文件
   * @param {string} projectId - 项目ID
   * @returns {Promise} 处理结果
   */
  async reprocessFile(projectId) {
    return await post(`/upload/process/${projectId}`)
  },

  /**
   * 获取文件类型验证
   * @param {string} filename - 文件名
   * @returns {Promise} 验证结果
   */
  async validateExtension(filename) {
    return await get(`/upload/validate-extension/${encodeURIComponent(filename)}`)
  },

  /**
   * 获取支持的文件类型列表
   * @returns {Promise} 支持的文件类型
   */
  async getSupportedFileTypes() {
    return await get('/upload/file-types')
  },

  /**
   * 获取上传状态
   * @param {string} taskId - 任务ID
   * @returns {Promise} 上传状态
   */
  async getUploadStatus(taskId) {
    return await get('/upload/status', { params: { task_id: taskId } })
  }
}

/**
 * 文件验证工具
 */
export const fileValidator = {
  /**
   * 验证文件类型
   * @param {File} file - 文件对象
   * @param {Array} allowedTypes - 允许的文件类型
   * @returns {boolean} 是否有效
   */
  isValidFileType(file, allowedTypes = ['.txt', '.md', '.docx', '.epub']) {
    const extension = '.' + file.name.split('.').pop().toLowerCase()
    return allowedTypes.includes(extension)
  },

  /**
   * 验证文件大小
   * @param {File} file - 文件对象
   * @param {number} maxSize - 最大大小（字节）
   * @returns {boolean} 是否有效
   */
  isValidFileSize(file, maxSize = 100 * 1024 * 1024) {
    return file.size <= maxSize
  },

  /**
   * 获取文件类型描述
   * @param {string} filename - 文件名
   * @returns {string} 文件类型描述
   */
  getFileTypeDescription(filename) {
    const extension = '.' + filename.split('.').pop().toLowerCase()
    const typeMap = {
      '.txt': 'TXT文档',
      '.md': 'Markdown文档',
      '.docx': 'Word文档',
      '.epub': 'EPUB电子书'
    }
    return typeMap[extension] || '未知文件类型'
  },

  /**
   * 格式化文件大小
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的大小
   */
  formatFileSize(bytes) {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  /**
   * 验证文件完整性
   * @param {File} file - 文件对象
   * @returns {Promise<boolean>} 是否完整
   */
  async validateFileIntegrity(file) {
    return new Promise((resolve) => {
      try {
        // 简单的文件读取验证
        const reader = new FileReader()
        reader.onload = () => resolve(true)
        reader.onerror = () => resolve(false)
        reader.readAsArrayBuffer(file.slice(0, 1024)) // 只读取前1KB验证
      } catch (error) {
        resolve(false)
      }
    })
  }
}

/**
 * 上传状态管理
 */
export class UploadManager {
  constructor() {
    this.uploads = new Map() // 存储上传任务
    this.listeners = new Set() // 监听器
  }

  /**
   * 添加上传任务
   * @param {string} id - 任务ID
   * @param {Object} uploadData - 上传数据
   */
  addUpload(id, uploadData) {
    this.uploads.set(id, {
      id,
      ...uploadData,
      status: 'pending',
      progress: 0,
      createdAt: new Date(),
      updatedAt: new Date()
    })
    this.notifyListeners()
  }

  /**
   * 更新上传进度
   * @param {string} id - 任务ID
   * @param {number} progress - 进度百分比
   */
  updateProgress(id, progress) {
    const upload = this.uploads.get(id)
    if (upload) {
      upload.progress = Math.min(100, Math.max(0, progress))
      upload.updatedAt = new Date()
      if (upload.progress === 100) {
        upload.status = 'completed'
      } else if (upload.progress > 0) {
        upload.status = 'uploading'
      }
      this.notifyListeners()
    }
  }

  /**
   * 设置上传状态
   * @param {string} id - 任务ID
   * @param {string} status - 状态
   * @param {Object} error - 错误信息
   */
  setStatus(id, status, error = null) {
    const upload = this.uploads.get(id)
    if (upload) {
      upload.status = status
      upload.error = error
      upload.updatedAt = new Date()
      this.notifyListeners()
    }
  }

  /**
   * 完成上传
   * @param {string} id - 任务ID
   * @param {Object} result - 上传结果
   */
  completeUpload(id, result) {
    const upload = this.uploads.get(id)
    if (upload) {
      upload.status = 'completed'
      upload.progress = 100
      upload.result = result
      upload.completedAt = new Date()
      upload.updatedAt = new Date()
      this.notifyListeners()
    }
  }

  /**
   * 失败上传
   * @param {string} id - 任务ID
   * @param {Object} error - 错误信息
   */
  failUpload(id, error) {
    const upload = this.uploads.get(id)
    if (upload) {
      upload.status = 'failed'
      upload.error = error
      upload.failedAt = new Date()
      upload.updatedAt = new Date()
      this.notifyListeners()
    }
  }

  /**
   * 获取上传任务
   * @param {string} id - 任务ID
   * @returns {Object|null} 上传任务
   */
  getUpload(id) {
    return this.uploads.get(id) || null
  }

  /**
   * 获取所有上传任务
   * @returns {Array} 上传任务列表
   */
  getAllUploads() {
    return Array.from(this.uploads.values())
  }

  /**
   * 获取进行中的上传任务
   * @returns {Array} 进行中的上传任务
   */
  getActiveUploads() {
    return this.getAllUploads().filter(
      upload => upload.status === 'pending' || upload.status === 'uploading'
    )
  }

  /**
   * 删除上传任务
   * @param {string} id - 任务ID
   */
  removeUpload(id) {
    this.uploads.delete(id)
    this.notifyListeners()
  }

  /**
   * 清理已完成的任务
   * @param {number} olderThan - 清理多少分钟前的任务
   */
  cleanup(olderThan = 30) {
    const cutoffTime = new Date(Date.now() - olderThan * 60 * 1000)
    for (const [id, upload] of this.uploads) {
      if (
        upload.completedAt &&
        upload.completedAt < cutoffTime &&
        (upload.status === 'completed' || upload.status === 'failed')
      ) {
        this.uploads.delete(id)
      }
    }
    this.notifyListeners()
  }

  /**
   * 添加状态监听器
   * @param {Function} listener - 监听器函数
   */
  addListener(listener) {
    this.listeners.add(listener)
  }

  /**
   * 移除状态监听器
   * @param {Function} listener - 监听器函数
   */
  removeListener(listener) {
    this.listeners.delete(listener)
  }

  /**
   * 通知所有监听器
   */
  notifyListeners() {
    const uploads = this.getAllUploads()
    this.listeners.forEach(listener => {
      try {
        listener(uploads)
      } catch (error) {
        console.error('Upload listener error:', error)
      }
    })
  }
}

// 创建全局上传管理器实例
export const uploadManager = new UploadManager()

// 定期清理已完成的任务
setInterval(() => {
  uploadManager.cleanup(60) // 清理1小时前的任务
}, 5 * 60 * 1000) // 每5分钟执行一次

// 导出单个函数以兼容现有导入
export const uploadFile = uploadService.uploadFile
export const uploadFromUrl = uploadService.uploadFromUrl
export const getPresignedUrl = uploadService.getPresignedUrl
export const deleteFile = uploadService.deleteFile
export const getFileInfo = uploadService.getFileInfo
export const reprocessFile = uploadService.reprocessFile
export const validateExtension = uploadService.validateExtension
export const getSupportedFileTypes = uploadService.getSupportedFileTypes
export const getUploadStatus = uploadService.getUploadStatus

export default uploadService