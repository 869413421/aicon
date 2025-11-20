<template>
  <div class="chapter-nav">
    <div class="nav-header">
      <h3>章节列表</h3>
      <el-button
        type="primary"
        size="small"
        :icon="Plus"
        @click="$emit('create')"
      >
        新建章节
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="搜索章节..."
        :prefix-icon="Search"
        size="small"
        clearable
      />
      <div class="filter-controls">
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          size="small"
          clearable
        >
          <el-option label="全部" value="" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="未确认" value="unconfirmed" />
        </el-select>
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          size="small"
        >
          <el-option label="章节序号" value="chapter_number" />
          <el-option label="创建时间" value="created_at" />
          <el-option label="更新时间" value="updated_at" />
        </el-select>
      </div>
    </div>

    <div v-if="loading" class="nav-loading">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="filteredChapters.length === 0" class="nav-empty">
      <el-empty description="暂无章节" :image-size="80" />
    </div>

    <div v-else class="nav-list">
      <div
        v-for="chapter in filteredChapters"
        :key="chapter.id"
        class="chapter-item"
        :class="{ 'is-selected': chapter.id === selectedId }"
        @click="$emit('select', chapter.id)"
      >
        <div class="chapter-number">{{ chapter.chapter_number }}</div>
        <div class="chapter-info">
          <div class="chapter-title">{{ chapter.title }}</div>
          <div class="chapter-meta">
            <span>{{ chapter.paragraph_count || 0 }} 段落</span>
            <span>{{ chapter.word_count || 0 }} 字</span>
          </div>
        </div>
        <div class="chapter-status">
          <el-tag
            v-if="chapter.is_confirmed"
            type="success"
            size="small"
            effect="plain"
          >
            已确认
          </el-tag>
        </div>
        <div class="chapter-actions" @click.stop>
          <el-dropdown trigger="click">
            <el-icon class="action-icon"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$emit('edit', chapter)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-dropdown-item>
                <el-dropdown-item @click="$emit('delete', chapter)" divided>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
    
    <!-- 加载更多按钮 - 移到列表外部 -->
    <div v-if="hasMore && !loading" class="load-more">
      <el-button
        size="small"
        @click="handleLoadMore"
        :loading="loading"
      >
        加载更多章节
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search, Plus, MoreFilled, Edit, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  chapters: {
    type: Array,
    default: () => []
  },
  selectedId: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasMore: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'create', 'edit', 'delete', 'load-more'])

const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('chapter_number')

// 获取滚动容器的引用
const navListRef = ref(null)

const filteredChapters = computed(() => {
  let result = [...props.chapters]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(chapter =>
      chapter.title?.toLowerCase().includes(query) ||
      chapter.chapter_number?.toString().includes(query)
    )
  }
  
  // 状态过滤
  if (statusFilter.value === 'confirmed') {
    result = result.filter(chapter => chapter.is_confirmed)
  } else if (statusFilter.value === 'unconfirmed') {
    result = result.filter(chapter => !chapter.is_confirmed)
  }
  
  // 排序
  result.sort((a, b) => {
    if (sortBy.value === 'chapter_number') {
      return (a.chapter_number || 0) - (b.chapter_number || 0)
    } else if (sortBy.value === 'created_at') {
      return new Date(b.created_at) - new Date(a.created_at)
    } else if (sortBy.value === 'updated_at') {
      return new Date(b.updated_at) - new Date(a.updated_at)
    }
    return 0
  })
  
  return result
})

// 处理加载更多
const handleLoadMore = () => {
  emit('load-more')
}
</script>

<style scoped>
.chapter-nav {
  width: 280px;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  overflow: hidden;
}

.nav-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--border-primary);
}

.nav-header h3 {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.nav-header .el-button {
  width: 100%;
  margin-bottom: var(--space-sm);
}

.filter-controls {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.filter-controls .el-select {
  flex: 1;
}

.nav-loading,
.nav-empty {
  padding: var(--space-lg);
}

.nav-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xs);
}

.load-more {
  padding: var(--space-md);
  text-align: center;
  border-top: 1px solid var(--border-primary);
}

.load-more .el-button {
  width: 100%;
}

.chapter-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-xs);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
  position: relative;
}

.chapter-item:hover {
  background: var(--bg-primary);
  border-color: var(--border-primary);
}

.chapter-item:hover .chapter-actions {
  opacity: 1;
}

.chapter-item.is-selected {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.chapter-item.is-selected .chapter-title,
.chapter-item.is-selected .chapter-meta {
  color: white;
}

.chapter-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--text-primary);
}

.chapter-item.is-selected .chapter-number {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.chapter-info {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.chapter-meta {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  display: flex;
  gap: var(--space-sm);
}

.chapter-status {
  flex-shrink: 0;
}

.chapter-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.chapter-item.is-selected .chapter-actions {
  opacity: 1;
}

.action-icon {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.action-icon:hover {
  background: var(--bg-primary);
  color: var(--primary-color);
}

.chapter-item.is-selected .action-icon {
  color: white;
}

.chapter-item.is-selected .action-icon:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 滚动条样式 */
.nav-list::-webkit-scrollbar {
  width: 6px;
}

.nav-list::-webkit-scrollbar-track {
  background: transparent;
}

.nav-list::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 3px;
}

.nav-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-disabled);
}
</style>
