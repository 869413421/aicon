<template>
  <div class="paragraph-stream">
    <div class="stream-header">
      <h3>段落编辑</h3>
      <div class="stream-actions">
        <el-button size="small" @click="handleCreateParagraph">
          <el-icon><Plus /></el-icon>
          新建段落
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="stream-loading">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="paragraphs.length === 0" class="stream-empty">
      <el-empty description="暂无段落">
        <el-button type="primary" @click="handleCreateParagraph">
          <el-icon><Plus /></el-icon>
          创建第一个段落
        </el-button>
      </el-empty>
    </div>

    <div v-else class="stream-content">
      <div
        v-for="(paragraph, index) in paragraphs"
        :key="paragraph.id"
        class="paragraph-block"
        :class="{
          'is-selected': paragraph.id === selectedId,
          'is-editing': paragraph.action === 'edit',
          'is-deleted': paragraph.action === 'delete'
        }"
        @click="handleSelect(paragraph.id)"
      >
        <div class="paragraph-header">
          <span class="paragraph-index">#{{ index + 1 }}</span>
          <el-radio-group
            :model-value="paragraph.action || 'keep'"
            @update:model-value="(val) => handleActionChange(paragraph.id, val)"
            @click.stop
            size="small"
          >
            <el-radio-button label="keep">保留</el-radio-button>
            <el-radio-button label="edit">编辑</el-radio-button>
            <el-radio-button label="delete">删除</el-radio-button>
          </el-radio-group>
        </div>

        <div class="paragraph-content">
          <div v-if="paragraph.action === 'edit'" class="content-editor">
            <el-input
              :model-value="paragraph.edited_content || paragraph.content"
              @update:model-value="(val) => handleContentChange(paragraph.id, val)"
              type="textarea"
              :rows="4"
              placeholder="请输入编辑后的内容"
            />
          </div>
          <div v-else class="content-display" :class="{ 'is-deleted': paragraph.action === 'delete' }">
            {{ paragraph.content }}
          </div>
        </div>

        <div class="paragraph-meta">
          <span>{{ paragraph.word_count || 0 }} 字</span>
          <span>{{ paragraph.sentence_count || 0 }} 句</span>
        </div>
      </div>
    </div>

    <!-- 创建段落对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建段落"
      width="600px"
    >
      <el-form>
        <el-form-item label="段落内容">
          <el-input
            v-model="newParagraphContent"
            type="textarea"
            :rows="6"
            placeholder="请输入段落内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  paragraphs: {
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
  }
})

const emit = defineEmits(['select', 'update', 'create'])

const createDialogVisible = ref(false)
const newParagraphContent = ref('')

const handleSelect = (paragraphId) => {
  emit('select', paragraphId)
}

const handleActionChange = (paragraphId, action) => {
  emit('update', paragraphId, { action })
}

const handleContentChange = (paragraphId, content) => {
  emit('update', paragraphId, { edited_content: content })
}

const handleCreateParagraph = () => {
  newParagraphContent.value = ''
  createDialogVisible.value = true
}

const handleConfirmCreate = () => {
  if (!newParagraphContent.value.trim()) {
    ElMessage.warning('请输入段落内容')
    return
  }
  
  emit('create', { content: newParagraphContent.value })
  createDialogVisible.value = false
}
</script>

<style scoped>
.paragraph-stream {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
}

.stream-header h3 {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.stream-loading,
.stream-empty {
  padding: var(--space-2xl);
}

.stream-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

.paragraph-block {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border: 2px solid var(--border-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.paragraph-block:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.paragraph-block.is-selected {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
}

.paragraph-block.is-editing {
  border-left: 4px solid var(--primary-color);
}

.paragraph-block.is-deleted {
  opacity: 0.6;
  border-left: 4px solid var(--danger-color);
}

.paragraph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border-primary);
}

.paragraph-index {
  font-weight: 700;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.paragraph-content {
  margin-bottom: var(--space-sm);
}

.content-display {
  font-size: var(--text-base);
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.content-display.is-deleted {
  text-decoration: line-through;
  color: var(--text-disabled);
}

.content-editor {
  margin: var(--space-sm) 0;
}

.paragraph-meta {
  display: flex;
  gap: var(--space-md);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

/* 滚动条样式 */
.stream-content::-webkit-scrollbar {
  width: 8px;
}

.stream-content::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.stream-content::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 4px;
}

.stream-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-disabled);
}
</style>
