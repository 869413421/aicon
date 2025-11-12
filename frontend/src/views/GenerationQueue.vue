<template>
  <div class="generation-queue-page">
    <div class="page-header">
      <h1>Content Generation Queue</h1>
      <p>View and manage AI content generation task queue</p>
    </div>

    <div class="queue-content">
      <el-card>
        <template #header>
          <h3>Generation Queue</h3>
        </template>

        <div class="empty-state">
          <el-empty description="No tasks in queue">
            <template #image>
              <el-icon size="64" color="#909399"><Timer /></el-icon>
            </template>
            <el-button type="primary">Create New Task</el-button>
          </el-empty>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { Timer } from '@element-plus/icons-vue'

// Component logic
console.log('GenerationQueue component loaded')
</script>

<style scoped>
.generation-queue-page {
  padding: var(--space-xl);
}

.page-header {
  margin-bottom: var(--space-2xl);
}

.page-header h1 {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.page-header p {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin: 0;
}

.queue-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.empty-state {
  padding: var(--space-4xl);
  text-align: center;
}
</style>