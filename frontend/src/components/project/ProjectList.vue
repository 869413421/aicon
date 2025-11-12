<template>
  <div class="project-list">
    <!-- 视图切换栏 -->
    <div class="view-header">
      <div class="header-left">
        <span class="project-count">
          共 {{ total }} 个项目
        </span>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            @click="viewMode = 'grid'"
            title="网格视图"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
          <el-button
            :type="viewMode === 'list' ? 'primary' : 'default'"
            @click="viewMode = 'list'"
            title="列表视图"
          >
            <el-icon><List /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && projects.length === 0" class="empty-state">
      <el-empty
        :description="'还没有项目，点击导航栏中的「新建项目」按钮开始吧！'"
        :image-size="120"
      />
    </div>

    <!-- 网格视图 -->
    <div v-else-if="viewMode === 'grid'" class="grid-view">
      <el-row :gutter="20">
        <el-col
          v-for="project in projects"
          :key="project.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
        >
          <ProjectCard
            :project="project"
            @edit="$emit('edit-project', $event)"
            @delete="$emit('delete-project', $event)"
            @view="$emit('view-project', $event)"
            @download="$emit('download-project', $event)"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 列表视图 -->
    <div v-else class="list-view">
      <el-table
        :data="projects"
        :row-key="(row) => row.id"
        @row-click="handleRowClick"
        stripe
        highlight-current-row
      >
        <el-table-column prop="title" label="项目标题" min-width="200">
          <template #default="{ row }">
            <div class="project-title">
              <el-text class="title-text" truncated>{{ row.title }}</el-text>
              <el-tag
                v-if="row.is_public"
                type="info"
                size="small"
                effect="plain"
              >
                公开
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
              effect="plain"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_processing_status" label="文件状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getFileStatusType(row.file_processing_status)"
              size="small"
              effect="plain"
            >
              {{ getFileStatusText(row.file_processing_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="word_count" label="字数" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ formatNumber(row.word_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="文件大小" width="120" align="right">
          <template #default="{ row }">
            <el-text>{{ formatFileSize(row.file_size) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <el-text>{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            <el-text>{{ formatDateTime(row.updated_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                type="primary"
                size="small"
                :icon="View"
                @click.stop="$emit('view-project', row)"
              >
                查看
              </el-button>
              <el-button
                type="default"
                size="small"
                :icon="Edit"
                @click.stop="$emit('edit-project', row)"
              >
                编辑
              </el-button>
              <el-dropdown @command="handleCommand">
                <el-button size="small" :icon="More">
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      :command="`download:${row.id}`"
                      :icon="Download"
                    >
                      下载文件
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`duplicate:${row.id}`"
                      :icon="CopyDocument"
                    >
                      复制项目
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`archive:${row.id}`"
                      :icon="FolderOpened"
                      :disabled="row.status === 'archived'"
                    >
                      {{ row.status === 'archived' ? '已归档' : '归档' }}
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`delete:${row.id}`"
                      :icon="Delete"
                      divided
                    >
                      删除项目
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Plus,
  Grid,
  List,
  View,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
} from '@element-plus/icons-vue'
import ProjectCard from './ProjectCard.vue'

// Props定义
const props = defineProps({
  projects: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  total: {
    type: Number,
    default: 0,
  },
  currentPage: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 20,
  },
})

// Emits定义
const emit = defineEmits([
  'edit-project',
  'delete-project',
  'view-project',
  'download-project',
  'duplicate-project',
  'archive-project',
  'page-change',
  'size-change',
  'row-click',
])

// 响应式数据
const viewMode = ref('grid')

// 方法

const handleSizeChange = (size) => {
  emit('size-change', size)
}

const handlePageChange = (page) => {
  emit('page-change', page)
}

const handleRowClick = (row) => {
  emit('row-click', row)
}

const handleCommand = async (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'download':
      emit('download-project', projectId)
      break
    case 'duplicate':
      await handleDuplicateProject(projectId)
      break
    case 'archive':
      await handleArchiveProject(projectId)
      break
    case 'delete':
      await handleDeleteProject(projectId)
      break
  }
}

const handleDuplicateProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要复制项目 "${project.title}" 吗？`,
      '确认复制',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    if (confirmed) {
      emit('duplicate-project', projectId)
      ElMessage.success('项目复制成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleArchiveProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要${project.status === 'archived' ? '取消归档' : '归档'}项目 "${project.title}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    if (confirmed) {
      emit('archive-project', projectId)
      ElMessage.success(project.status === 'archived' ? '项目已取消归档' : '项目已归档')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleDeleteProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要删除项目 "${project.title}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger',
      }
    )

    if (confirmed) {
      emit('delete-project', projectId)
      ElMessage.success('项目删除成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

// 工具方法
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    archived: 'info',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    archived: '已归档',
  }
  return textMap[status] || status
}

const getFileStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    uploading: 'warning',
    uploaded: 'success',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return typeMap[status] || 'info'
}

const getFileStatusText = (status) => {
  const textMap = {
    pending: '等待',
    uploading: '上传中',
    uploaded: '已上传',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return textMap[status] || status
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 暴露给父组件的方法
defineExpose({
  getViewMode: () => viewMode.value,
})
</script>

<style scoped>
.project-list {
  width: 100%;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 0 4px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.loading-container {
  padding: 20px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.grid-view {
  margin: -10px;
}

.list-view {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  flex: 1;
  min-width: 0;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 0;
  }
}
</style>