/**
 * 项目管理状态管理
 * 使用Pinia管理项目相关的状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { projectsAPI, filesAPI, projectUtils } from '@/services/projects'
import { uploadService, uploadManager } from '@/services/upload'

export const useProjectsStore = defineStore('projects', () => {
  // 状态定义
  const projects = ref([])
  const currentProject = ref(null)
  const statistics = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 分页状态
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    totalPages: 0
  })

  // 搜索和过滤状态
  const searchQuery = ref('')
  const statusFilter = ref('')
  const sortBy = ref('created_at')
  const sortOrder = ref('desc')

  // 文件内容状态
  const fileContent = ref('')
  const contentLoading = ref(false)
  const contentError = ref(null)

  // 上传任务状态
  const uploadTasks = ref([])
  const activeUploads = computed(() => {
    return uploadTasks.value.filter(task =>
      task.status === 'pending' || task.status === 'uploading'
    )
  })

  // 计算属性
  const filteredProjects = computed(() => {
    let result = projects.value

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(project =>
        project.title.toLowerCase().includes(query) ||
        (project.description && project.description.toLowerCase().includes(query))
      )
    }

    if (statusFilter.value) {
      result = result.filter(project => project.status === statusFilter.value)
    }

    return result
  })

  const projectsByStatus = computed(() => {
    const groups = {}
    projects.value.forEach(project => {
      if (!groups[project.status]) {
        groups[project.status] = []
      }
      groups[project.status].push(project)
    })
    return groups
  })

  const recentProjects = computed(() => {
    return [...projects.value]
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      .slice(0, 5)
  })

  const hasUnprocessedFiles = computed(() => {
    return projects.value.some(project =>
      project.file_processing_status !== 'completed'
    )
  })

  // 方法
  /**
   * 获取项目列表
   * @param {Object} params - 查询参数
   */
  const fetchProjects = async (params = {}) => {
    try {
      loading.value = true
      error.value = null

      const queryParams = {
        page: pagination.value.page,
        size: pagination.value.size,
        search: searchQuery.value,
        status: statusFilter.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value,
        ...params
      }

      const response = await projectsAPI.getProjects(queryParams)

      projects.value = response.projects || []
      pagination.value = {
        page: response.page || queryParams.page,
        size: response.size || queryParams.size,
        total: response.total || 0,
        totalPages: response.total_pages || Math.ceil(response.total / queryParams.size)
      }

      return response

    } catch (err) {
      error.value = err.message || '获取项目列表失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取项目详情
   * @param {string} projectId - 项目ID
   */
  const fetchProjectById = async (projectId) => {
    try {
      loading.value = true
      error.value = null

      const project = await projectsAPI.getProjectById(projectId)
      currentProject.value = project

      // 更新列表中的项目数据
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = project
      }

      return project

    } catch (err) {
      error.value = err.message || '获取项目详情失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建项目
   * @param {Object} projectData - 项目数据
   */
  const createProject = async (projectData) => {
    try {
      loading.value = true
      error.value = null

      const project = await projectsAPI.createProject(projectData)

      // 添加到列表开头
      projects.value.unshift(project)
      pagination.value.total += 1

      ElMessage.success('项目创建成功')
      return project

    } catch (err) {
      error.value = err.message || '创建项目失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新项目
   * @param {string} projectId - 项目ID
   * @param {Object} updateData - 更新数据
   */
  const updateProject = async (projectId, updateData) => {
    try {
      loading.value = true
      error.value = null

      const updatedProject = await projectsAPI.updateProject(projectId, updateData)

      // 更新列表中的项目
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }

      // 更新当前项目
      if (currentProject.value?.id === projectId) {
        currentProject.value = updatedProject
      }

      ElMessage.success('项目更新成功')
      return updatedProject

    } catch (err) {
      error.value = err.message || '更新项目失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除项目
   * @param {string} projectId - 项目ID
   * @param {boolean} permanent - 是否永久删除
   */
  const deleteProject = async (projectId, permanent = false) => {
    try {
      loading.value = true
      error.value = null

      await projectsAPI.deleteProject(projectId, permanent)

      // 从列表中移除
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value.splice(index, 1)
        pagination.value.total -= 1
      }

      // 清除当前项目
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
      }

      ElMessage.success('项目删除成功')

    } catch (err) {
      error.value = err.message || '删除项目失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 下载项目文件
   * @param {string} projectId - 项目ID
   */
  const downloadProject = async (projectId) => {
    try {
      const response = await projectsAPI.downloadProject(projectId)

      if (response.download_url) {
        // 创建下载链接
        const link = document.createElement('a')
        link.href = response.download_url
        link.download = response.filename || `project_${projectId}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }

      return response

    } catch (err) {
      error.value = err.message || '下载文件失败'
      ElMessage.error(error.value)
      throw err
    }
  }

  /**
   * 重新处理项目文件
   * @param {string} projectId - 项目ID
   */
  const reprocessProject = async (projectId) => {
    try {
      loading.value = true
      error.value = null

      await uploadService.reprocessFile(projectId)

      // 更新项目状态
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index].file_processing_status = 'processing'
        projects.value[index].processing_progress = 0
      }

      if (currentProject.value?.id === projectId) {
        currentProject.value.file_processing_status = 'processing'
        currentProject.value.processing_progress = 0
      }

      ElMessage.success('重新处理请求已发送')

    } catch (err) {
      error.value = err.message || '重新处理失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取项目文件内容
   * @param {string} projectId - 项目ID
   */
  const fetchProjectContent = async (projectId) => {
    try {
      contentLoading.value = true
      contentError.value = null

      // 临时实现：返回模拟内容
      fileContent.value = `文件内容预览功能正在开发中...`

      return fileContent.value

    } catch (err) {
      contentError.value = err.message || '获取文件内容失败'
      ElMessage.error(contentError.value)
      throw err
    } finally {
      contentLoading.value = false
    }
  }

  /**
   * 设置搜索条件
   * @param {Object} filters - 过滤条件
   */
  const setFilters = (filters = {}) => {
    if (filters.search !== undefined) searchQuery.value = filters.search
    if (filters.status !== undefined) statusFilter.value = filters.status
    if (filters.sortBy !== undefined) sortBy.value = filters.sortBy
    if (filters.sortOrder !== undefined) sortOrder.value = filters.sortOrder
  }

  /**
   * 重置状态
   */
  const resetState = () => {
    projects.value = []
    currentProject.value = null
    statistics.value = null
    loading.value = false
    error.value = null
    searchQuery.value = ''
    statusFilter.value = ''
    fileContent.value = ''
    contentLoading.value = false
    contentError.value = null
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      totalPages: 0
    }
  }

  // 向后兼容的方法名称
  const fetchProject = fetchProjectById

  return {
    // 状态
    projects,
    currentProject,
    statistics,
    loading,
    error,
    pagination,
    searchQuery,
    statusFilter,
    sortBy,
    sortOrder,
    fileContent,
    contentLoading,
    contentError,
    uploadTasks,

    // 计算属性
    filteredProjects,
    projectsByStatus,
    recentProjects,
    hasUnprocessedFiles,
    activeUploads,

    // 方法（包含向后兼容的别名）
    fetchProjects,
    fetchProject, // 向后兼容
    fetchProjectById, // 新方法
    createProject,
    updateProject,
    deleteProject,
    downloadProject,
    reprocessProject,
    fetchProjectContent,
    setFilters,
    resetState,

    // 工具函数
    formatProjectStatus: projectUtils.formatProjectStatus,
    formatFileStatus: projectUtils.formatFileStatus,
    formatFileType: projectUtils.formatFileType,
    formatNumber: projectUtils.formatNumber,
    formatFileSize: projectUtils.formatFileSize,
    formatDateTime: projectUtils.formatDateTime,
    formatRelativeTime: projectUtils.formatRelativeTime,
    canPerformOperation: projectUtils.canPerformOperation
  }
})