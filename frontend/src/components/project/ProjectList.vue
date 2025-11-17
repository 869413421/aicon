<template>
  <div class="project-list">
    <!-- 视图切换栏 -->
    <div class="view-header">
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
            @view="$emit('view-project', $event)"
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

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <div class="status-cell">
              <el-tag
                :type="projectsStore.getStatusType(row.status)"
                size="small"
                effect="plain"
              >
                {{ projectsStore.getStatusText(row.status) }}
              </el-tag>
              <!-- 进度条 -->
              <div
                v-if="row.processing_progress > 0 && row.processing_progress < 100"
                class="progress-bar"
              >
                <div
                  class="progress-fill"
                  :style="{ width: row.processing_progress + '%' }"
                ></div>
              </div>
            </div>
          </template>
        </el-table-column>


        <el-table-column prop="word_count" label="字数" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatNumber(row.word_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="paragraph_count" label="段落" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatNumber(row.paragraph_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="sentence_count" label="句子" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatNumber(row.sentence_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="chapter_count" label="章节" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatNumber(row.chapter_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="文件大小" width="120" align="right">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatFileSize(row.file_size) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            <el-text>{{ projectsStore.formatDateTime(row.updated_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="primary"
                size="small"
                :icon="View"
                link
                @click.stop="$emit('view-project', row)"
              >
                查看
              </el-button>
              <el-button
                v-if="row.status === 'failed'"
                type="warning"
                size="small"
                :icon="RefreshRight"
                link
                @click.stop="$emit('retry-project', row)"
              >
                重试
              </el-button>
              <el-button
                v-if="projectsStore.isEditable(row)"
                type="default"
                size="small"
                :icon="Edit"
                link
                @click.stop="$emit('edit-project', row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="projectsStore.isArchivable(row)"
                type="warning"
                size="small"
                link
                @click.stop="$emit('archive-project', row)"
              >
                归档
              </el-button>
            </div>
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
  RefreshRight,
} from '@element-plus/icons-vue'
import ProjectCard from './ProjectCard.vue'
import { useProjectsStore } from '@/stores/projects'

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

// Store实例
const projectsStore = useProjectsStore()

// Emits定义
const emit = defineEmits([
  'edit-project',
  'archive-project',
  'view-project',
  'retry-project',
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


// 使用store中的工具方法，避免重复代码

// 暴露给父组件的方法
defineExpose({
  getViewMode: () => viewMode.value,
})
</script>

<style scoped>
.project-list {
  width: 100%;
  padding: var(--space-md);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.project-count {
  font-size: var(--text-base);
  color: var(--text-secondary);
  font-weight: 600;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.loading-container {
  padding: var(--space-xl);
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
}

.empty-state {
  padding: var(--space-2xl) var(--space-lg);
  text-align: center;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.grid-view {
  width: 100%;
  overflow: visible; /* 确保内容不被裁剪 */
  padding: var(--space-lg) 0;
}

.grid-view .el-col {
  padding: var(--space-lg);
}

/* Element Plus Row 组件可能需要的额外样式 */
:deep(.el-row) {
  width: 100%;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
}

/* 确保卡片容器有足够的空间 */
:deep(.el-col) {
  position: relative;
  overflow: visible;
}

/* 确保ProjectCard组件完全可见 */
.grid-view .project-card {
  position: relative;
  z-index: 1;
}

/* 表格样式优化 */
.list-view {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  padding: var(--space-lg);
}

:deep(.el-table) {
  --el-table-border-color: var(--border-primary);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.03);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-primary);
  font-size: var(--text-sm);
}

:deep(.el-table th) {
  font-weight: 600;
  font-size: var(--text-sm);
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-bottom: 2px solid var(--border-primary);
  padding: var(--space-md) var(--space-sm);
  color: var(--text-primary);
}

:deep(.el-table td) {
  border-bottom: 1px solid var(--border-primary);
  padding: var(--space-lg) var(--space-sm);
  vertical-align: middle;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(99, 102, 241, 0.02);
}

:deep(.el-table__body tr:hover > td) {
  background: rgba(99, 102, 241, 0.03) !important;
}

/* 表格行悬停效果 */
:deep(.el-table__row) {
  transition: all var(--transition-fast);
}

:deep(.el-table__row:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.project-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.title-text {
  flex: 1;
  min-width: 0;
  font-weight: 600;
  color: var(--text-primary);
}

/* 状态单元格和进度条 */
.status-cell {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  align-items: flex-start;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
  transition: width 0.3s ease;
  border-radius: var(--radius-full);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
  justify-content: flex-end;
}

.action-buttons :deep(.el-button--link) {
  padding: var(--space-xs) var(--space-sm);
  margin: 0;
  min-height: auto;
  border: none;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.action-buttons :deep(.el-button--link:hover) {
  transform: translateY(-1px);
  background: rgba(99, 102, 241, 0.05);
  border-radius: var(--radius-md);
}

.action-buttons :deep(.el-button--danger.is-link:hover) {
  background: rgba(245, 108, 108, 0.05);
  color: var(--danger-color);
}

/* 分页样式优化 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: var(--space-xl);
  padding: var(--space-xl) 0;
}

:deep(.el-pagination) {
  --el-pagination-button-bg-color: var(--bg-primary);
  --el-pagination-button-color: var(--text-primary);
  --el-pagination-hover-color: var(--primary-color);
  --el-pagination-bg-color: var(--bg-primary);
  --el-pagination-border-radius: var(--radius-lg);
  --el-pagination-font-size: var(--text-sm);
}

:deep(.el-pagination .el-pager li) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  margin: 0 2px;
}

:deep(.el-pagination .el-pager li:hover) {
  border-color: var(--primary-color);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

/* 按钮组样式 */
:deep(.el-button-group) {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

:deep(.el-button-group .el-button) {
  border-radius: 0;
  border-right: none;
}

:deep(.el-button-group .el-button:first-child) {
  border-top-left-radius: var(--radius-lg);
  border-bottom-left-radius: var(--radius-lg);
}

:deep(.el-button-group .el-button:last-child) {
  border-top-right-radius: var(--radius-lg);
  border-bottom-right-radius: var(--radius-lg);
  border-right: 1px solid var(--border-primary);
}

:deep(.el-button-group .el-button--primary) {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border-color: var(--primary-color);
}

/* 视图切换按钮优化 */
:deep(.el-button-group .el-button) {
  transition: all var(--transition-base);
}

:deep(.el-button-group .el-button:hover) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* 标签样式优化 */
:deep(.el-tag) {
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: var(--text-xs);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--border-primary);
}

:deep(.el-tag--info) {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  border-color: rgba(99, 102, 241, 0.3);
}

:deep(.el-tag--success) {
  background: rgba(67, 197, 138, 0.1);
  color: var(--success-color);
  border-color: rgba(67, 197, 138, 0.3);
}

:deep(.el-tag--warning) {
  background: rgba(230, 162, 60, 0.1);
  color: var(--warning-color);
  border-color: rgba(230, 162, 60, 0.3);
}

:deep(.el-tag--danger) {
  background: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);
  border-color: rgba(245, 108, 108, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-list {
    padding: var(--space-sm);
  }

  .view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
    padding: 0;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .project-count {
    order: -1;
  }

  .grid-view {
    width: 100%;
    overflow: visible;
  }

  .grid-view .el-col {
    padding: var(--space-sm);
  }

  .loading-container,
  .empty-state {
    padding: var(--space-lg) var(--space-md);
  }

  .list-view {
    padding: var(--space-md);
  }

  :deep(.el-table) {
    font-size: var(--text-sm);
  }

  :deep(.el-table th),
  :deep(.el-table td) {
    padding: var(--space-sm);
  }

  .pagination-container {
    padding: var(--space-lg) 0;
    margin-top: var(--space-lg);
  }

  :deep(.el-button-group .el-button) {
    padding: var(--space-xs) var(--space-sm);
    font-size: var(--text-xs);
  }
}

@media (max-width: 480px) {
  .project-list {
    padding: var(--space-xs);
  }

  .view-header {
    gap: var(--space-sm);
  }

  .project-count {
    font-size: var(--text-sm);
    padding: var(--space-xs) var(--space-sm);
  }

  .loading-container,
  .empty-state {
    padding: var(--space-md);
  }

  :deep(.el-table) {
    font-size: var(--text-xs);
  }

  :deep(.el-table th),
  :deep(.el-table td) {
    padding: var(--space-xs);
  }

  .project-title {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }

  .action-buttons {
    flex-direction: column;
    gap: var(--space-xs);
    align-items: flex-end;
  }

  .action-buttons :deep(.el-button--link) {
    padding: var(--space-xs) var(--space-xs);
    font-size: var(--text-xs);
    min-width: auto;
  }

  .list-view {
    padding: var(--space-sm);
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  :deep(.el-table) {
    --el-table-border-color: var(--border-primary);
    --el-table-header-bg-color: var(--bg-dark);
    --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.1);
  }

  :deep(.el-descriptions) {
    --el-descriptions-table-border: 1px solid var(--border-primary);
    --el-descriptions-item-bordered-background: var(--bg-dark);
  }
}
</style>