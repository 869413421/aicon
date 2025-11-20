<template>
  <div class="paragraph-item" :class="itemClass">
    <div class="item-header">
      <div class="header-left">
        <span class="index-badge">#{{ index }}</span>
        <span class="status-badge" :class="paragraph.action">
          {{ statusText }}
        </span>
      </div>
      <div class="header-actions">
        <el-radio-group 
          :model-value="paragraph.action" 
          @update:model-value="handleActionChange"
          size="small"
        >
          <el-radio-button label="keep">保留</el-radio-button>
          <el-radio-button label="edit">编辑</el-radio-button>
          <el-radio-button label="delete">删除</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="item-content">
      <!-- 原始内容展示 -->
      <div class="content-block original" v-if="showOriginal">
        <div class="label">原始内容</div>
        <div class="text">{{ paragraph.content }}</div>
      </div>

      <!-- 编辑/展示区域 -->
      <div class="content-block current">
        <div class="label">
          {{ paragraph.action === 'edit' ? '编辑内容' : '当前内容' }}
        </div>
        
        <!-- 编辑模式 -->
        <el-input
          v-if="paragraph.action === 'edit'"
          :model-value="paragraph.edited_content"
          @update:model-value="handleContentChange"
          type="textarea"
          :rows="4"
          placeholder="请输入修改后的内容"
          resize="vertical"
        />
        
        <!-- 展示模式 -->
        <div v-else class="text" :class="textClass">
          {{ paragraph.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  paragraph: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:action', 'update:content', 'update:ignore-reason'])

// 计算属性
const itemClass = computed(() => ({
  'is-modified': props.paragraph.action !== 'keep',
  'is-deleted': props.paragraph.action === 'delete',
  'is-editing': props.paragraph.action === 'edit'
}))

const statusText = computed(() => {
  const map = {
    keep: '保留',
    edit: '编辑',
    delete: '删除'
  }
  return map[props.paragraph.action] || '未知'
})

const showOriginal = computed(() => {
  return props.paragraph.action === 'edit' || props.paragraph.action === 'delete'
})

const textClass = computed(() => ({
  'text-deleted': props.paragraph.action === 'delete'
}))

// 事件处理
const handleActionChange = (val) => {
  emit('update:action', props.paragraph.id, val)
}

const handleContentChange = (val) => {
  emit('update:content', props.paragraph.id, val)
}
</script>

<style scoped>
.paragraph-item {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  transition: all var(--transition-fast);
}

.paragraph-item:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary-color);
}

.paragraph-item.is-modified {
  border-left: 4px solid var(--warning-color);
}

.paragraph-item.is-deleted {
  border-left-color: var(--danger-color);
  opacity: 0.8;
}

.paragraph-item.is-editing {
  border-left-color: var(--primary-color);
  background: var(--bg-primary);
  box-shadow: var(--shadow-md);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.index-badge {
  font-weight: 700;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.status-badge {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.status-badge.keep { color: var(--success-color); background: rgba(103, 194, 58, 0.1); }
.status-badge.edit { color: var(--primary-color); background: rgba(64, 158, 255, 0.1); }
.status-badge.delete { color: var(--danger-color); background: rgba(245, 108, 108, 0.1); }

.item-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.content-block {
  position: relative;
}

.content-block .label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
  font-weight: 500;
}

.content-block.original {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-primary);
}

.text {
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.text-deleted {
  text-decoration: line-through;
  color: var(--text-disabled);
}
</style>
