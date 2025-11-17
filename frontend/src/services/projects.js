/**
 * 项目管理服务 - 简洁实现，严格按照规范
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
   * 创建新项目（支持文件信息）
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
   * @returns {Promise} 删除结果
   */
  async deleteProject(projectId) {
    return await del(`/projects/${projectId}`)
  },

  /**
   * 获取项目文件内容
   * @param {string} projectId - 项目ID
   * @returns {Promise} 文件内容
   */
  async getProjectFileContent(projectId) {
    return await get(`/projects/${projectId}/content`)
  },

  /**
   * 下载项目文件
   * @param {string} projectId - 项目ID
   * @returns {Promise} 下载结果
   */
  async downloadProjectFile(projectId) {
    return await get(`/projects/${projectId}/download`)
  },

  /**
   * 复制项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 复制的项目
   */
  async duplicateProject(projectId) {
    return await post(`/projects/${projectId}/duplicate`)
  },

  /**
   * 归档项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 归档后的项目
   */
  async archiveProject(projectId) {
    return await put(`/projects/${projectId}/archive`)
  },

  /**
   * 重试失败的项目
   * @param {string} projectId - 项目ID
   * @returns {Promise} 重试结果
   */
  async retryProject(projectId) {
    return await post(`/projects/${projectId}/retry`)
  },

  /**
   * 获取项目状态详情
   * @param {string} projectId - 项目ID
   * @returns {Promise} 项目状态详情
   */
  async getProjectStatus(projectId) {
    return await get(`/projects/${projectId}/status`)
  }
}

/**
 * 项目状态工具 - 简洁实现，匹配后端数据模型
 */
export const projectUtils = {
  /**
   * 获取状态文本
   * @param {string} status - 状态值
   * @returns {string} 状态文本
   */
  getStatusText(status) {
    const statusMap = {
      'uploaded': '已上传',
      'parsing': '解析中',
      'parsed': '解析完成',
      'generating': '生成中',
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
      'uploaded': 'info',
      'parsing': 'warning',
      'parsed': 'success',
      'generating': 'warning',
      'completed': 'success',
      'failed': 'danger',
      'archived': 'info'
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
    } else if (project.status === 'generating') {
      return project.processing_progress || 50
    } else if (project.status === 'parsed') {
      return 40
    } else if (project.status === 'parsing') {
      return 20
    } else if (project.status === 'uploaded') {
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
    return !['parsing', 'generating', 'archived'].includes(project.status)
  },

  /**
   * 检查项目是否可删除
   * @param {Object} project - 项目对象
   * @returns {boolean} 是否可删除
   */
  isDeletable(project) {
    return !['parsing', 'generating'].includes(project.status)
  },

  /**
   * 检查项目是否可归档
   * @param {Object} project - 项目对象
   * @returns {boolean} 是否可归档
   */
  isArchivable(project) {
    return !['parsing', 'generating', 'archived'].includes(project.status)
  },

  /**
   * 获取状态图标
   * @param {string} status - 状态值
   * @returns {string} 图标名称
   */
  getStatusIcon(status) {
    const iconMap = {
      'uploaded': 'Upload',
      'parsing': 'Loading',
      'parsed': 'CircleCheck',
      'generating': 'VideoPlay',
      'completed': 'SuccessFilled',
      'failed': 'CircleClose'
    }
    return iconMap[status] || 'Document'
  }
}

export default projectsService