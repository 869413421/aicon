<template>
  <div class="projects-page">
    <!-- 页面头部信息 -->
    <div class="page-header">
      <h1 class="page-title">项目管理</h1>
      <p class="page-description">管理和查看您的所有项目</p>
    </div>

    <!-- 操作栏 -->
    <div class="actions-bar">
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
        <el-option label="已上传" value="uploaded" />
        <el-option label="解析中" value="parsing" />
        <el-option label="解析完成" value="parsed" />
        <el-option label="生成中" value="generating" />
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
      <div class="action-buttons">
        <el-button type="primary" @click="handleCreateProject" :icon="Plus">
          新建项目
        </el-button>
        <el-button @click="handleRefreshProjects" :icon="Refresh">
          刷新
        </el-button>
      </div>
    </div>

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
        @archive-project="handleArchiveProject"
        @retry-project="handleRetryProject"
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

    <!-- 编辑项目对话框 -->
    <el-dialog
      v-model="showEditorDialog"
      title="编辑项目"
      width="600px"
      :close-on-click-modal="false"
      @close="handleEditorClose"
    >
      <ProjectEditor
        ref="projectEditorRef"
        :project="editingProject"
        :loading="editorLoading"
        @submit="handleEditorSubmit"
        @cancel="handleEditorCancel"
        @error="handleEditorError"
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
  import { Plus, Refresh, Search } from '@element-plus/icons-vue'

  // 组件导入
  import ProjectList from '@/components/project/ProjectList.vue'
  import ProjectDetail from '@/components/project/ProjectDetail.vue'
  import ProjectCreator from '@/components/project/ProjectCreator.vue'
  import ProjectEditor from '@/components/project/ProjectEditor.vue'

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
  const showEditorDialog = ref(false)
  const showContentDialog = ref(false)

  // 创建器状态
  const projectCreatorRef = ref()
  const creatorLoading = ref(false)

  // 编辑器状态
  const projectEditorRef = ref()
  const editorLoading = ref(false)
  const editingProject = ref(null)

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
    editingProject.value = project
    showEditorDialog.value = true
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

  
  const handleRetryProject = async (project) => {
    try {
      await projectsStore.retryProject(project.id)

      // 重试成功后刷新项目列表
      loadProjects()

      // 如果当前在查看该项目详情，也刷新详情
      if (selectedProjectId.value === project.id) {
        loadProjectDetail(project.id)
      }

    } catch (error) {
      console.error('重试项目失败:', error)
      // 错误消息已经在store中处理了
    }
  }

  const handleReprocess = async (project) => {
    // 向后兼容，使用重试功能
    await handleRetryProject(project)
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

  const handleRefreshProjects = () => {
    loadProjects()
  }

  // 创建器处理
  const handleCreatorSubmit = async (creatorData) => {
    try {
      creatorLoading.value = true

      // ProjectCreator 组件已经处理了文件上传和项目创建，并显示了成功消息
      // 这里只需要处理成功后的UI更新
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

  // 归档功能处理
  const handleArchiveProject = async (project) => {
    try {
      await ElMessageBox.confirm(
        `确定要归档项目 "${project.title}" 吗？归档后项目将停止所有处理任务，此操作不可恢复。`,
        '确认归档',
        {
          confirmButtonText: '确定归档',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--warning'
        }
      )

      await projectsStore.archiveProject(project.id)
      ElMessage.success('项目归档成功')

      // 重新加载列表
      loadProjects()

      // 如果归档的是当前查看的项目，返回列表
      if (selectedProjectId.value === project.id) {
        handleBackToList()
      }

    } catch (error) {
      if (error !== 'cancel') {
        console.error('归档项目失败:', error)
        ElMessage.error('归档项目失败')
      }
    }
  }

  // 编辑器处理
  const handleEditorSubmit = async (updatedProject) => {
    try {
      editorLoading.value = true

      // 关闭编辑对话框
      showEditorDialog.value = false
      editingProject.value = null

      // 重新加载列表和项目详情
      loadProjects()
      if (selectedProjectId.value) {
        await loadProjectDetail(selectedProjectId.value)
      }

    } catch (error) {
      console.error('编辑项目失败:', error)
      ElMessage.error(error.message || '编辑项目失败')
    } finally {
      editorLoading.value = false
    }
  }

  const handleEditorCancel = () => {
    showEditorDialog.value = false
    editingProject.value = null
  }

  const handleEditorClose = () => {
    projectEditorRef.value?.resetForm()
    editingProject.value = null
  }

  const handleEditorError = (error) => {
    console.error('编辑器错误:', error)
    ElMessage.error(error.message || '编辑器处理失败')
  }

  </script>

<style scoped>
.projects-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
}

.page-description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

.actions-bar {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  flex-wrap: wrap;
}

.action-buttons {
  display: flex;
  gap: var(--space-sm);
  margin-left: auto;
}

.list-view {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.detail-view {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  overflow: hidden;
}

.content-loading {
  padding: var(--space-lg);
}

.content-preview {
  max-height: 96vh;
  overflow: auto;
  padding: var(--space-lg);
}

.file-content {
  font-size: var(--text-sm);
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  background: var(--bg-secondary);
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.content-error {
  padding: var(--space-lg);
}

/* 响应式设计 */
@media (max-width: 968px) {
  .actions-bar {
    padding: var(--space-md);
  }

  .action-buttons {
    width: 100%;
    margin-left: 0;
    margin-top: var(--space-md);
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .page-header {
    gap: 2px;
  }

  .page-title {
    font-size: var(--text-lg);
  }

  .page-description {
    font-size: var(--text-xs);
  }

  .actions-bar {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-sm);
  }

  .action-buttons {
    margin-top: var(--space-sm);
  }

  .action-buttons :deep(.el-button) {
    flex: 1;
  }
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .actions-bar,
  .list-view,
  .detail-view {
    background: var(--bg-dark);
    border-color: var(--border-primary);
  }

  .file-content {
    background: var(--bg-dark);
    border-color: var(--border-primary);
  }
}
</style>