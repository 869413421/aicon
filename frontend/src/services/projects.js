/**
 * 项目管理服务
 */

import { get, post, put, del } from './api'

/**
 * 项目管理服务
 */
export const projectsService = {
  /**
   * 获取用户项目列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 项目列表和总数
   */
  async getProjects(params = {}) {
    return await get('/projects/', { params })
  },

  /**
   * 根据ID获取项目详情
   * @param {string} projectId - 项目ID
   * @returns {Promise} 项目详情
   */
  async getProjectById(projectId) {
    return await get(`/projects/${projectId}`)
  },

  /**
   * 创建新项目
   * @param {Object} projectData - 项目数据
   * @returns {Promise} 创建的项目
   */
  async createProject(projectData) {
    return await post('/projects/', projectData)
  },

  /**
   * 更新项目
   * @param {string} projectId - 项目ID
   * @param {Object} updateData - 更新数据
   * @returns {Promise} 更新后的项目
   */
  async updateProject(projectId, updateData) {
    return await put(`/projects/${projectId}`, updateData)
  },

  /**
   * 删除项目
   * @param {string} projectId - 项目ID
   * @param {Object} params - 删除参数
   * @returns {Promise} 删除结果
   */
  async deleteProject(projectId, params = {}) {
    return await del(`/projects/${projectId}`, { params })
  },

  /**
   * 恢复已删除的项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 恢复结果
   */
  async restoreProject(projectId) {
    return await post(`/projects/${projectId}/restore`)
  },

  /**
   * 搜索项目
   * @param {Object} searchParams - 搜索参数
   * @returns {Promise} 搜索结果
   */
  async searchProjects(searchParams) {
    const { q, filters = {}, page = 1, size = 20 } = searchParams

    const params = {
      q,
      page,
      size,
      ...filters
    }

    return await get('/projects/search', { params })
  },

  /**
   * 获取项目统计信息
   * @returns {Promise} 统计数据
   */
  async getProjectStatistics() {
    return await get('/projects/statistics/summary')
  },

  /**
   * 下载项目文件
   * @param {string} projectId - 项目ID
   * @returns {Promise} 文件下载响应
   */
  async downloadProjectFile(projectId) {
    return await get(`/projects/${projectId}/download`)
  },

  /**
   * 复制项目
   * @param {string} projectId - 项目ID
   * @param {Object} copyData - 复制参数
   * @returns {Promise} 复制结果
   */
  async duplicateProject(projectId, copyData) {
    return await post(`/projects/${projectId}/duplicate`, copyData)
  },

  /**
   * 归档项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 归档结果
   */
  async archiveProject(projectId) {
    return await post(`/projects/${projectId}/archive`)
  },

  /**
   * 取消归档项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 取消归档结果
   */
  async unarchiveProject(projectId) {
    return await post(`/projects/${projectId}/unarchive`)
  }
}

/**
 * 项目状态工具
 */
export const projectUtils = {
  /**
   * 获取状态文本
   * @param {string} status - 状态值
   * @returns {string} 状态文本
   */
  getStatusText(status) {
    const statusMap = {
      'draft': '草稿',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败',
      'archived': '已归档'
    }
    return statusMap[status] || status
  },

  /**
   * 获取状态类型（用于UI组件）
   * @param {string} status - 状态值
   * @returns {string} Element Plus状态类型
   */
  getStatusType(status) {
    const typeMap = {
      'draft': 'info',
      'processing': 'warning',
      'completed': 'success',
      'failed': 'danger',
      'archived': 'info'
    }
    return typeMap[status] || 'info'
  },

  /**
   * 获取文件处理状态文本
   * @param {string} status - 处理状态
   * @returns {string} 状态文本
   */
  getProcessingStatusText(status) {
    const statusMap = {
      'pending': '等待',
      'uploading': '上传中',
      'uploaded': '已上传',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败'
    }
    return statusMap[status] || status
  },

  /**
   * 获取文件处理状态类型
   * @param {string} status - 处理状态
   * @returns {string} Element Plus状态类型
   */
  getProcessingStatusType(status) {
    const typeMap = {
      'pending': 'info',
      'uploading': 'warning',
      'uploaded': 'success',
      'processing': 'warning',
      'completed': 'success',
      'failed': 'danger'
    }
    return typeMap[status] || 'info'
  },

  /**
   * 格式化文件大小
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的大小
   */
  formatFileSize(bytes) {
    if (!bytes) return '-'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  /**
   * 格式化项目时间
   * @param {string} dateTime - 时间字符串
   * @returns {string} 格式化的时间
   */
  formatDateTime(dateTime) {
    if (!dateTime) return '-'
    const date = new Date(dateTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  },

  /**
   * 格式化数字
   * @param {number} num - 数字
   * @returns {string} 格式化后的数字
   */
  formatNumber(num) {
    if (!num) return '0'
    return num.toLocaleString()
  },

  /**
   * 计算项目完成进度
   * @param {Object} project - 项目对象
   * @returns {number} 完成进度百分比
   */
  calculateProgress(project) {
    if (project.status === 'completed') {
      return 100
    } else if (project.status === 'processing') {
      return project.processing_progress || 0
    } else if (project.file_processing_status === 'completed') {
      return 80
    } else if (project.file_processing_status === 'processing') {
      return 60 + (project.processing_progress || 0) * 0.4
    } else if (project.file_processing_status === 'uploaded') {
      return 60
    } else if (project.file_processing_status === 'uploading') {
      return 20 + (project.processing_progress || 0) * 0.4
    } else if (project.file_processing_status === 'pending') {
      return 10
    } else {
      return 0
    }
  },

  /**
   * 检查项目是否可编辑
   * @param {Object} project - 项目对象
   * @returns {boolean} 是否可编辑
   */
  isEditable(project) {
    return project.status !== 'processing' && project.file_processing_status !== 'processing'
  },

  /**
   * 检查项目是否可删除
   * @param {Object} project - 项目对象
   * @returns {boolean} 是否可删除
   */
  isDeletable(project) {
    return project.status !== 'processing' && project.file_processing_status !== 'processing'
  },

  /**
   * 获取状态图标
   * @param {string} status - 状态值
   * @returns {string} 图标名称
   */
  getStatusIcon(status) {
    const iconMap = {
      'draft': 'Edit',
      'processing': 'Loading',
      'completed': 'CircleCheck',
      'failed': 'CircleClose',
      'archived': 'FolderOpened'
    }
    return iconMap[status] || 'Document'
  }
}

// 保持与现有代码的兼容性，导出原有API
export const projectsAPI = {
  getProjects: projectsService.getProjects,
  searchProjects: projectsService.searchProjects,
  getProjectById: projectsService.getProjectById,
  createProject: projectsService.createProject,
  updateProject: projectsService.updateProject,
  deleteProject: projectsService.deleteProject,
  restoreProject: projectsService.restoreProject,
  getProjectStatistics: projectsService.getProjectStatistics,
  downloadProject: projectsService.downloadProjectFile,
  duplicateProject: projectsService.duplicateProject
}

export const filesAPI = {
  cleanupOrphanedFiles: async (params = {}) => {
    return await del('/files/cleanup/orphaned', { params })
  },
  getStorageUsage: async () => {
    return await get('/files/storage/usage')
  },
  listUserFiles: async (params = {}) => {
    return await get('/files/list', { params })
  },
  batchDeleteFiles: async (objectKeys) => {
    return await post('/files/batch-delete', { object_keys: objectKeys })
  },
  checkFileIntegrity: async (params = {}) => {
    return await get('/files/integrity/check', { params })
  }
}

export default projectsService