<template>
  <div class="page-navigation">
    <div class="nav-content">
      <!-- 左侧：返回按钮和页面信息 -->
      <div class="nav-left">
        <el-button
          v-if="showBack"
          @click="handleBack"
          class="back-button secondary-btn"
          :size="buttonSize"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span>{{ backText }}</span>
        </el-button>
        <div class="page-info">
          <h1 class="page-title">
            <el-icon v-if="showIcon" class="title-icon"><component :is="titleIcon" /></el-icon>
            {{ title }}
          </h1>
          <p v-if="description" class="page-description">{{ description }}</p>
        </div>
      </div>

      <!-- 右侧：操作区域 -->
      <div class="nav-right">
        <div v-if="$slots.extra" class="extra-content">
          <slot name="extra"></slot>
        </div>

        <!-- 用户信息显示 -->
        <div v-if="showUserInfo && user" class="user-dropdown">
          <el-dropdown @command="handleUserAction" trigger="click">
            <div class="user-info">
              <el-avatar :size="36" :src="user.avatar_url" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-details">
                <span class="username">{{ user.display_name || user.username }}</span>
                <span class="user-status">在线</span>
              </div>
              <el-icon class="expand-icon">
                <ArrowDown />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>个人资料</span>
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  <span>系统设置</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 面包屑导航 -->
    <div v-if="breadcrumbs && breadcrumbs.length > 0" class="breadcrumb-container">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item
          v-for="(item, index) in breadcrumbs"
          :key="index"
          :to="item.path"
        >
          <el-icon v-if="item.icon" class="breadcrumb-icon">
            <component :is="item.icon" />
          </el-icon>
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowLeft, ArrowDown, User, Setting, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Props定义
const props = defineProps({
  // 页面基本信息
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  titleIcon: {
    type: [String, Object],
    default: null
  },
  showIcon: {
    type: Boolean,
    default: false
  },

  // 返回按钮配置
  showBack: {
    type: Boolean,
    default: true
  },
  backText: {
    type: String,
    default: '返回'
  },
  backPath: {
    type: [String, Function],
    default: null
  },

  // 按钮大小
  buttonSize: {
    type: String,
    default: 'default',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  },

  // 面包屑导航
  breadcrumbs: {
    type: Array,
    default: () => [],
    validator: (value) => {
      return value.every(item =>
        typeof item === 'object' &&
        'title' in item &&
        typeof item.title === 'string'
      )
    }
  },

  // 用户信息
  showUserInfo: {
    type: Boolean,
    default: false
  },

  // 紧凑模式
  compact: {
    type: Boolean,
    default: false
  }
})

// Emits定义
const emit = defineEmits(['back'])

const router = useRouter()
const authStore = useAuthStore()

// 计算用户信息
const user = computed(() => authStore.user)

// 处理返回操作
const handleBack = () => {
  if (props.backPath) {
    if (typeof props.backPath === 'function') {
      props.backPath()
    } else {
      router.push(props.backPath)
    }
  } else if (emit && typeof emit === 'function') {
    emit('back')
  } else {
    router.go(-1)
  }
}

// 处理用户操作
const handleUserAction = (command) => {
  switch (command) {
    case 'profile':
      router.push('/settings')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 处理退出登录
const handleLogout = async () => {
  try {
    await authStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    console.error('退出登录失败:', error)
    ElMessage.error('退出登录失败')
  }
}
</script>

<style scoped>
.page-navigation {
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  margin-bottom: var(--space-lg);
  position: relative;
  overflow: hidden;
}

.nav-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg) var(--space-xl);
  position: relative;
  z-index: 1;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.back-button {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-sm) var(--space-lg);
  font-weight: 600;
  color: var(--text-primary);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.back-button:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
  transform: translateY(-1px);
}

.page-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.title-icon {
  color: var(--primary-color);
  padding: var(--space-xs);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.1);
  font-size: 20px;
}

.page-description {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
}

.extra-content {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  position: relative;
}

.user-info:hover {
  background: rgba(99, 102, 241, 0.05);
}

.user-avatar {
  box-shadow: var(--shadow-sm);
  border: 2px solid var(--bg-primary);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.username {
  font-weight: 600;
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.user-status {
  font-size: var(--text-xs);
  color: var(--success-color);
  font-weight: 500;
}

.user-status::before {
  content: '●';
  margin-right: 2px;
  font-size: 8px;
}

.expand-icon {
  font-size: 14px;
  color: var(--text-secondary);
  transition: transform var(--transition-base);
  margin-left: var(--space-xs);
}

.user-info:hover .expand-icon {
  color: var(--primary-color);
}

/* 下拉菜单样式 */
.el-dropdown-menu {
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-lg);
  padding: var(--space-xs);
  min-width: 160px;
}

.el-dropdown-menu .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  margin: var(--space-xs) 0;
  transition: all var(--transition-base);
  font-weight: 500;
}

.el-dropdown-menu .el-dropdown-menu__item:hover {
  background: rgba(99, 102, 241, 0.05);
  color: var(--primary-color);
  transform: translateX(2px);
}

.el-dropdown-menu .el-dropdown-menu__item .el-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.el-dropdown-menu .el-dropdown-menu__item.is-divided {
  border-top: 1px solid var(--border-primary);
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  color: var(--danger-color);
}

.el-dropdown-menu .el-dropdown-menu__item.is-divided:hover {
  background: rgba(239, 68, 68, 0.05);
  color: var(--danger-color);
}

.breadcrumb-container {
  padding: var(--space-md) var(--space-xl) var(--space-lg);
  background: linear-gradient(135deg, var(--bg-primary), rgba(99, 102, 241, 0.02));
  border-top: 1px solid var(--border-primary);
}

.breadcrumb-icon {
  margin-right: var(--space-xs);
  color: var(--text-secondary);
  font-size: 14px;
}

/* 紧凑模式 */
.page-navigation.compact .nav-content {
  padding: var(--space-md) var(--space-lg);
}

.page-navigation.compact .page-title {
  font-size: var(--text-lg);
}

.page-navigation.compact .page-description {
  font-size: var(--text-xs);
}

.page-navigation.compact .breadcrumb-container {
  padding: var(--space-sm) var(--space-lg) var(--space-md);
}

/* 响应式设计 */
@media (max-width: 968px) {
  .nav-content {
    padding: var(--space-md);
  }

  .nav-right {
    gap: var(--space-md);
  }

  .nav-left {
    gap: var(--space-md);
  }

  .back-button span {
    display: none;
  }

  .page-title {
    font-size: var(--text-lg);
  }

  .page-description {
    display: none;
  }

  .username {
    display: none;
  }

  .extra-content {
    gap: var(--space-sm);
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .nav-content {
    padding: var(--space-sm) var(--space-md);
  }

  .page-title {
    font-size: var(--text-base);
    max-width: 200px;
  }

  .title-icon {
    font-size: 16px;
  }

  .extra-content {
    gap: var(--space-xs);
    justify-content: flex-end;
  }

  .extra-content :deep(.el-input) {
    max-width: 150px;
  }

  .extra-content :deep(.el-select) {
    max-width: 100px;
  }

  .extra-content :deep(.el-button) span {
    display: none;
  }
}

@media (max-width: 480px) {
  .nav-content {
    padding: var(--space-sm);
  }

  .nav-left {
    gap: var(--space-sm);
  }

  .page-title {
    font-size: var(--text-sm);
    max-width: 120px;
  }

  .breadcrumb-container {
    padding: var(--space-sm) var(--space-md) var(--space-sm);
  }
}

/* 动画 */
@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-navigation {
  animation: slide-up 0.5s ease-out;
}

/* 深色主题支持 */
@media (prefers-color-scheme: dark) {
  .page-navigation {
    background: var(--bg-dark);
    border-color: var(--gray-700);
  }

  .nav-content {
    background: linear-gradient(135deg, var(--bg-dark), rgba(99, 102, 241, 0.02));
  }

  .breadcrumb-container {
    background: linear-gradient(135deg, var(--bg-dark), rgba(99, 102, 241, 0.02));
    border-top-color: var(--gray-700);
  }
}

/* 焦点和无障碍 */
.back-button:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--primary-color);
  position: relative;
  z-index: 10;
}

.user-info:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--primary-color);
  position: relative;
  z-index: 10;
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .page-navigation {
    border-width: 2px;
  }

  .back-button {
    border-width: 2px;
  }

  .back-button:hover {
    border-width: 3px;
  }
}

/* 减少动画偏好支持 */
@media (prefers-reduced-motion: reduce) {
  .page-navigation {
    animation: none;
  }

  .back-button,
  .user-info,
  .expand-icon {
    transition: none;
  }
}
</style>