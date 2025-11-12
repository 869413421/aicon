<template>
  <div class="projects-page">
    <!-- 统一导航头部 -->
    <PageNavigation
      :title="pageTitle"
      description="管理和查看您的所有项目"
      :back-text="'返回控制台'"
      :back-path="goToDashboard"
      :show-user-info="true"
      :show-icon="true"
      :title-icon="Folder"
      :breadcrumbs="breadcrumbs"
    >
      <template #extra>
        <!-- 搜索框 -->
        <el-input
          v-model="searchQuery"
          placeholder="搜索项目标题或描述..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 240px"
        />

        <!-- 状态筛选 -->
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          @change="handleStatusFilter"
          style="width: 120px"
        >
          <el-option label="全部" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="处理中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已归档" value="archived" />
        </el-select>

        <!-- 排序方式 -->
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          @change="handleSort"
          style="width: 120px"
        >
          <el-option label="创建时间" value="created_at" />
          <el-option label="标题" value="title" />
          <el-option label="更新时间" value="updated_at" />
          <el-option label="文件大小" value="file_size" />
        </el-select>

        <!-- 操作按钮 -->
        <el-button type="primary" @click="handleCreateProject" :icon="Plus">
          新建项目
        </el-button>
        <el-button @click="handleRefreshProjects" :icon="Refresh">
          刷新
        </el-button>
      </template>
    </PageNavigation>

    <!-- 项目列表视图 -->
    <div v-if="currentView === 'list'" class="list-view">
      <ProjectList
        :projects="projects"
        :loading="loading"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        @edit-project="handleEditProject"
        @delete-project="handleDeleteProject"
        @view-project="handleViewProject"
        @download-project="handleDownloadProject"
        @duplicate-project="handleDuplicateProject"
        @archive-project="handleArchiveProject"
        @page-change="handlePageChange"
        @size-change="handleSizeChange"
        @row-click="handleRowClick"
      />
    </div>

    <!-- 项目详情视图 -->
    <div v-else-if="currentView === 'detail'" class="detail-view">
      <ProjectDetail
        :project-id="selectedProjectId"
        :project="selectedProject"
        :loading="detailLoading"
        :error="detailError"
        @back="handleBackToList"
        @edit="handleEditProject"
        @delete="handleDeleteProject"
        @download="handleDownloadProject"
        @duplicate="handleDuplicateProject"
        @archive="handleArchiveProject"
        @reprocess="handleReprocess"
        @refresh="handleRefreshProject"
        @start-generation="handleStartGeneration"
        @view-content="handleViewContent"
      />
    </div>

    <!-- 创建项目对话框 -->
    <el-dialog
      v-model="showCreatorDialog"
      title="创建新项目"
      width="600px"
      :close-on-click-modal="false"
      @close="handleCreatorClose"
    >
      <ProjectCreator
        ref="projectCreatorRef"
        :loading="creatorLoading"
        @submit="handleCreatorSubmit"
        @cancel="handleCreatorCancel"
        @error="handleCreatorError"
      />
    </el-dialog>

    <!-- 文件内容预览对话框 -->
    <el-dialog
      v-model="showContentDialog"
      title="文件内容预览"
      width="80%"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div v-if="contentLoading" class="content-loading">
        <el-skeleton :rows="10" animated />
      </div>
      <div v-else-if="fileContent" class="content-preview">
        <pre class="file-content">{{ fileContent }}</pre>
      </div>
      <div v-else-if="contentError" class="content-error">
        <el-result
          icon="error"
          title="加载失败"
          :sub-title="contentError"
        >
          <template #extra>
            <el-button @click="loadFileContent">重新加载</el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
  import { computed, onMounted, ref, watch } from 'vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import { ArrowLeft, Plus, Refresh, House, Folder, Search } from '@element-plus/icons-vue'

  // 组件导入
  import PageNavigation from '@/components/common/PageNavigation.vue'
  import ProjectList from '@/components/project/ProjectList.vue'
  import ProjectDetail from '@/components/project/ProjectDetail.vue'
  import ProjectCreator from '@/components/project/ProjectCreator.vue'
  import { uploadService } from '@/services/upload'

  // 状态管理导入
  import { useProjectsStore } from '@/stores/projects'
  import { useAuthStore } from '@/stores/auth'

  // Store实例
  const projectsStore = useProjectsStore()
  const authStore = useAuthStore()

  // 视图状态
  const currentView = ref('list') // 'list' | 'detail'
  const selectedProjectId = ref(null)
  const selectedProject = ref(null)

  // 对话框状态
  const showCreatorDialog = ref(false)
  const showContentDialog = ref(false)

  // 创建器状态
  const projectCreatorRef = ref()
  const creatorLoading = ref(false)

  // 列表状态
  const loading = ref(false)
  const projects = ref([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // 详情状态
  const detailLoading = ref(false)
  const detailError = ref(null)

  // 文件内容状态
  const contentLoading = ref(false)
  const fileContent = ref('')
  const contentError = ref(null)

  // 搜索和过滤状态
  const searchQuery = ref('')
  const statusFilter = ref('')
  const sortBy = ref('created_at')
  const sortOrder = ref('desc')

  // 计算属性
  const pageTitle = computed(() => {
    if (currentView.value === 'detail' && selectedProject.value) {
      return selectedProject.value.title
    }
    return '项目管理'
  })

  // 面包屑导航
  const breadcrumbs = computed(() => {
    if (currentView.value === 'detail' && selectedProject.value) {
      return [
        { title: '首页', path: '/dashboard', icon: House },
        { title: '项目管理', path: '/projects' },
        { title: selectedProject.value.title }
      ]
    }
    return [
      { title: '首页', path: '/dashboard', icon: House },
      { title: '项目管理' }
    ]
  })

  // 监听路由参数变化
  watch(() => selectedProjectId.value, (newId) => {
    if (newId) {
      loadProjectDetail(newId)
    }
  })

  // 生命周期
  onMounted(() => {
    loadProjects()
  })

  // 方法
  const loadProjects = async (params = {}) => {
    try {
      loading.value = true

      const queryParams = {
        page: currentPage.value,
        size: pageSize.value,
        search: searchQuery.value,
        project_status: statusFilter.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value,
        ...params
      }

      const response = await projectsStore.fetchProjects(queryParams)
      projects.value = response.projects
      total.value = response.total

    } catch (error) {
      console.error('加载项目列表失败:', error)
      ElMessage.error('加载项目列表失败')
    } finally {
      loading.value = false
    }
  }

  const loadProjectDetail = async (projectId) => {
    try {
      detailLoading.value = true
      detailError.value = null

      selectedProject.value = await projectsStore.fetchProjectById(projectId)

    } catch (error) {
      console.error('加载项目详情失败:', error)
      detailError.value = error.message || '加载项目详情失败'
      ElMessage.error('加载项目详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  const loadFileContent = async () => {
    if (!selectedProject.value) return

    try {
      contentLoading.value = true
      contentError.value = null

      fileContent.value = await projectsStore.fetchProjectContent(selectedProject.value.id)

    } catch (error) {
      console.error('加载文件内容失败:', error)
      contentError.value = error.message || '加载文件内容失败'
      ElMessage.error('加载文件内容失败')
    } finally {
      contentLoading.value = false
    }
  }

  // 列表操作处理
  const handleCreateProject = () => {
    showCreatorDialog.value = true
  }

  const handleEditProject = (project) => {
    // 导航到项目详情页面进行编辑
    handleViewProject(project)
  }

  const handleDeleteProject = async (project) => {
    try {
      await ElMessageBox.confirm(
        `确定要删除项目 "${project.title}" 吗？此操作不可恢复。`,
        '确认删除',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'error',
          confirmButtonClass: 'el-button--danger'
        }
      )

      await projectsStore.deleteProject(project.id)
      ElMessage.success('项目删除成功')

      // 如果删除的是当前查看的项目，返回列表
      if (selectedProjectId.value === project.id) {
        handleBackToList()
      }

      // 重新加载列表
      loadProjects()

    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除项目失败:', error)
        ElMessage.error('删除项目失败')
      }
    }
  }

  const handleViewProject = (project) => {
    selectedProjectId.value = project.id
    currentView.value = 'detail'
  }

  const handleDownloadProject = async (project) => {
    try {
      await projectsStore.downloadProject(project.id)
      ElMessage.success('文件下载已开始')
    } catch (error) {
      console.error('下载文件失败:', error)
      ElMessage.error('下载文件失败')
    }
  }

  const handleDuplicateProject = async (project) => {
    try {
      const newProject = await projectsStore.duplicateProject(project.id)
      ElMessage.success('项目复制成功')
      loadProjects()
    } catch (error) {
      console.error('复制项目失败:', error)
      ElMessage.error('复制项目失败')
    }
  }

  const handleArchiveProject = async (project) => {
    try {
      const isArchive = project.status !== 'archived'
      await projectsStore.archiveProject(project.id, isArchive)
      ElMessage.success(isArchive ? '项目已归档' : '项目已取消归档')
      loadProjects()
    } catch (error) {
      console.error('归档项目失败:', error)
      ElMessage.error('归档项目失败')
    }
  }

  const handleReprocess = async (project) => {
    try {
      await projectsStore.reprocessProject(project.id)
      ElMessage.success('重新处理请求已发送')
      if (selectedProject.value) {
        loadProjectDetail(project.id)
      }
    } catch (error) {
      console.error('重新处理失败:', error)
      ElMessage.error('重新处理失败')
    }
  }

  const handleBackToList = () => {
    currentView.value = 'list'
    selectedProjectId.value = null
    selectedProject.value = null
    detailError.value = null
  }

  const handleRefreshProject = (projectId) => {
    loadProjectDetail(projectId)
  }

  const handleStartGeneration = (project) => {
    ElMessage.info('视频生成功能即将上线')
  }

  const handleViewContent = (project) => {
    selectedProject.value = project
    showContentDialog.value = true
    loadFileContent()
  }

  // 搜索和过滤处理
  const handleSearch = (query) => {
    searchQuery.value = query
    currentPage.value = 1
    loadProjects()
  }

  const handleStatusFilter = (status) => {
    statusFilter.value = status
    currentPage.value = 1
    loadProjects()
  }

  const handleSort = ({ field, order }) => {
    sortBy.value = field
    sortOrder.value = order
    currentPage.value = 1
    loadProjects()
  }

  const handlePageChange = (page) => {
    currentPage.value = page
    loadProjects()
  }

  const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
    loadProjects()
  }

  const handleRowClick = (row) => {
    handleViewProject(row)
  }

  const goToDashboard = () => {
    // 返回控制台
    window.location.href = '/dashboard'
  }

  const handleRefreshProjects = () => {
    loadProjects()
  }

  // 创建器处理
  const handleCreatorSubmit = async (creatorData) => {
    try {
      creatorLoading.value = true

      // 创建FormData用于文件上传
      const formData = new FormData()
      formData.append('file', creatorData.file)
      formData.append('title', creatorData.title)
      if (creatorData.description) {
        formData.append('description', creatorData.description)
      }
      formData.append('auto_process', creatorData.auto_process)

      // 调用上传API
      const response = await uploadService.uploadFile({ formData })

      ElMessage.success('项目创建成功')
      showCreatorDialog.value = false
      loadProjects()

    } catch (error) {
      console.error('创建项目失败:', error)
      ElMessage.error(error.message || '创建项目失败')
    } finally {
      creatorLoading.value = false
    }
  }

  const handleCreatorCancel = () => {
    showCreatorDialog.value = false
  }

  const handleCreatorClose = () => {
    projectCreatorRef.value?.resetForm()
  }

  const handleCreatorError = (error) => {
    console.error('创建器错误:', error)
    ElMessage.error(error.message || '创建器处理失败')
  }

  // 页面标题更新
  watch(pageTitle, (newTitle) => {
    document.title = newTitle
  }, { immediate: true })
</script>

<style scoped>
  .projects-page {
    @apply min-h-screen bg-gray-50;
  }

  .list-view {
    @apply container mx-auto px-4 py-6;
  }

  .detail-view {
    @apply min-h-screen bg-white;
  }

  .content-loading {
    @apply p-6;
  }

  .content-preview {
    @apply max-h-96 overflow-auto;
  }

  .file-content {
    @apply text-sm text-gray-700 leading-relaxed whitespace-pre-wrap;
    font-family: 'Courier New', monospace;
  }

  .content-error {
    @apply p-6;
  }

  @media (max-width: 768px) {
    .list-view {
      @apply px-2 py-4;
    }
  }
</style>