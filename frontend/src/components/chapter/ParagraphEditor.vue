<template>
  <div class="paragraph-editor">
    <div class="editor-header">
      <div class="header-left">
        <h3>段落编辑</h3>
        <span class="paragraph-count">共 {{ paragraphs.length }} 个段落</span>
      </div>
      <div class="header-actions">
        <el-button @click="fetchParagraphs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="handleBatchSave" :loading="saving">
          <el-icon><Check /></el-icon>
          保存修改
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="paragraphs-list">
      <div
        v-for="(paragraph, index) in paragraphs"
        :key="paragraph.id"
        class="paragraph-item"
        :class="{ 'is-modified': isModified(paragraph) }"
      >
        <div class="paragraph-header">
          <span class="paragraph-index">#{{ index + 1 }}</span>
          <div class="paragraph-actions">
            <el-radio-group v-model="paragraph.action" size="small">
              <el-radio-button label="keep">保留</el-radio-button>
              <el-radio-button label="edit">编辑</el-radio-button>
              <el-radio-button label="delete">删除</el-radio-button>
              <el-radio-button label="ignore">忽略</el-radio-button>
            </el-radio-group>
          </div>
        </div>

        <div class="paragraph-content">
          <!-- 原始内容 -->
          <div class="original-content" v-if="paragraph.action !== 'keep'">
            <div class="label">原始内容:</div>
            <div class="text">{{ paragraph.content }}</div>
          </div>

          <!-- 编辑区域 -->
          <div class="edit-area">
            <div class="label" v-if="paragraph.action !== 'keep'">
              {{ paragraph.action === 'edit' ? '编辑内容:' : '当前内容:' }}
            </div>
            <el-input
              v-if="paragraph.action === 'edit'"
              v-model="paragraph.edited_content"
              type="textarea"
              :rows="3"
              placeholder="请输入修改后的内容"
            />
            <div
              v-else
              class="text"
              :class="{
                'text-deleted': paragraph.action === 'delete',
                'text-ignored': paragraph.action === 'ignore'
              }"
            >
              {{ paragraph.content }}
            </div>
          </div>

          <!-- 忽略原因 -->
          <div v-if="paragraph.action === 'ignore'" class="ignore-reason">
            <el-input
              v-model="paragraph.ignore_reason"
              placeholder="请输入忽略原因（可选）"
              size="small"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'
import paragraphsService from '@/services/paragraphs'

const props = defineProps({
  chapterId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['saved'])

const loading = ref(false)
const saving = ref(false)
const paragraphs = ref([])
const originalParagraphs = ref([])

// 获取段落列表
const fetchParagraphs = async () => {
  loading.value = true
  try {
    const response = await paragraphsService.getParagraphs(props.chapterId)
    paragraphs.value = response.paragraphs.map(p => ({
      ...p,
      // 如果没有编辑过的内容，默认使用原始内容
      edited_content: p.edited_content || p.content
    }))
    // 保存原始数据的副本，用于检测修改
    originalParagraphs.value = JSON.parse(JSON.stringify(paragraphs.value))
  } catch (error) {
    console.error('获取段落失败:', error)
    ElMessage.error('获取段落列表失败')
  } finally {
    loading.value = false
  }
}

// 检测段落是否被修改
const isModified = (paragraph) => {
  const original = originalParagraphs.value.find(p => p.id === paragraph.id)
  if (!original) return false

  return (
    paragraph.action !== original.action ||
    paragraph.edited_content !== original.edited_content ||
    paragraph.ignore_reason !== original.ignore_reason
  )
}

// 批量保存
const handleBatchSave = async () => {
  const modifiedParagraphs = paragraphs.value.filter(isModified)
  
  if (modifiedParagraphs.length === 0) {
    ElMessage.info('没有需要保存的修改')
    return
  }

  saving.value = true
  try {
    await paragraphsService.batchUpdateParagraphs(props.chapterId, modifiedParagraphs)
    ElMessage.success(`成功保存 ${modifiedParagraphs.length} 个段落的修改`)
    // 重新获取列表以更新状态
    await fetchParagraphs()
    emit('saved')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存修改失败')
  } finally {
    saving.value = false
  }
}

// 监听章节ID变化
watch(() => props.chapterId, (newId) => {
  if (newId) {
    fetchParagraphs()
  }
})

onMounted(() => {
  if (props.chapterId) {
    fetchParagraphs()
  }
})
</script>

<style scoped>
.paragraph-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  height: 100%;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-primary);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: var(--space-md);
}

.header-left h3 {
  margin: 0;
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.paragraph-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.paragraphs-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  overflow-y: auto;
  padding-right: var(--space-sm);
}

.paragraph-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  transition: all var(--transition-fast);
}

.paragraph-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.paragraph-item.is-modified {
  border-left: 3px solid var(--warning-color);
  background: linear-gradient(to right, rgba(230, 162, 60, 0.05), transparent);
}

.paragraph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.paragraph-index {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.paragraph-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.text {
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
}

.text-deleted {
  text-decoration: line-through;
  color: var(--text-disabled);
}

.text-ignored {
  color: var(--text-disabled);
  font-style: italic;
}

.original-content {
  padding: var(--space-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border-primary);
}

.ignore-reason {
  margin-top: var(--space-sm);
}
</style>
