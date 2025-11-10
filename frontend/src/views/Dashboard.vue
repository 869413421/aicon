<template>
  <div class="dashboard">
    <!-- 顶部工具栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="welcome-section">
          <h1 class="dashboard-title">
            <el-icon size="20" class="title-icon"><VideoPlay /></el-icon>
            内容创作工作台
          </h1>
          <p class="welcome-text">欢迎回来，{{ authStore.user?.display_name || authStore.user?.username }}！开始您的创作之旅</p>
        </div>
      </div>
      <div class="header-right">
        <div class="action-buttons">
          <el-button @click="$router.push('/projects')" class="secondary-btn">
            <el-icon><Folder /></el-icon>
            项目管理
          </el-button>
          <el-button type="primary" @click="$router.push('/generation')" class="primary-btn">
            <el-icon><VideoPlay /></el-icon>
            开始创作
          </el-button>
        </div>
        <el-dropdown @command="handleUserAction" trigger="click" class="user-dropdown">
          <div class="user-info">
            <el-avatar :size="36" :src="authStore.user?.avatar_url" class="user-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <div class="user-details">
              <span class="username">{{ authStore.user?.display_name || authStore.user?.username }}</span>
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

    <!-- 快速操作入口 -->
    <div class="quick-actions">
      <div class="section-header">
        <h2>快速操作</h2>
        <p>选择您需要的功能，快速开始创作</p>
      </div>
      <div class="action-grid">
        <div class="quick-action primary-action modern-gradient-1" @click="$router.push('/generation')">
          <div class="action-icon-large">
            <el-icon size="32"><VideoPlay /></el-icon>
          </div>
          <div class="action-content">
            <h3>开始创作</h3>
            <p>AI 文本转视频</p>
          </div>
          <div class="action-badge">推荐</div>
          <div class="action-glow"></div>
        </div>

        <div class="quick-action modern-gradient-2" @click="$router.push('/projects')">
          <div class="action-icon">
            <el-icon size="24"><Folder /></el-icon>
          </div>
          <div class="action-content">
            <h4>项目管理</h4>
            <p>{{ 0 }} 个项目</p>
          </div>
          <div class="action-arrow">
            <el-icon size="16"><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="quick-action modern-gradient-3" @click="$router.push('/publish')">
          <div class="action-icon">
            <el-icon size="24"><Promotion /></el-icon>
          </div>
          <div class="action-content">
            <h4>内容分发</h4>
            <p>一键发布</p>
          </div>
          <div class="action-arrow">
            <el-icon size="16"><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="quick-action modern-gradient-4" @click="$router.push('/settings')">
          <div class="action-icon">
            <el-icon size="24"><Setting /></el-icon>
          </div>
          <div class="action-content">
            <h4>系统设置</h4>
            <p>配置管理</p>
          </div>
          <div class="action-arrow">
            <el-icon size="16"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 左侧：统计和最近项目 -->
      <div class="left-column">
        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="mini-stat">
            <div class="mini-stat-icon projects">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="mini-stat-info">
              <div class="mini-stat-number">0</div>
              <div class="mini-stat-label">项目</div>
            </div>
          </div>

          <div class="mini-stat">
            <div class="mini-stat-icon tasks">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="mini-stat-info">
              <div class="mini-stat-number">0</div>
              <div class="mini-stat-label">进行中</div>
            </div>
          </div>

          <div class="mini-stat">
            <div class="mini-stat-icon videos">
              <el-icon><Share /></el-icon>
            </div>
            <div class="mini-stat-info">
              <div class="mini-stat-number">0</div>
              <div class="mini-stat-label">已发布</div>
            </div>
          </div>

          <div class="mini-stat">
            <div class="mini-stat-icon cost">
              <el-icon><Money /></el-icon>
            </div>
            <div class="mini-stat-info">
              <div class="mini-stat-number">¥0</div>
              <div class="mini-stat-label">总成本</div>
            </div>
          </div>
        </div>

        <!-- 最近项目 -->
        <div class="recent-projects">
          <div class="section-header">
            <h3>最近项目</h3>
            <el-button link @click="$router.push('/projects')">查看全部</el-button>
          </div>
          <div class="projects-list">
            <div class="empty-projects">
              <el-icon size="32"><Document /></el-icon>
              <p>暂无项目</p>
              <el-button type="primary" plain @click="$router.push('/projects')">
                创建第一个项目
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：任务队列和活动 -->
      <div class="right-column">
        <!-- 任务队列 -->
        <div class="task-queue">
          <div class="section-header">
            <h3>
              <el-icon><Timer /></el-icon>
              生成队列
            </h3>
            <el-button link @click="$router.push('/generation')">管理</el-button>
          </div>
          <div class="queue-content">
            <div class="empty-queue">
              <el-icon size="32"><VideoCamera /></el-icon>
              <p>队列为空</p>
              <el-button type="primary" plain @click="$router.push('/generation')">
                开始生成视频
              </el-button>
            </div>
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="recent-activity">
          <div class="section-header">
            <h3>
              <el-icon><Clock /></el-icon>
              最近活动
            </h3>
          </div>
          <div class="activity-list">
            <div class="empty-activity">
              <el-icon size="32"><Document /></el-icon>
              <p>暂无活动记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import {
  User,
  Folder,
  VideoPlay,
  Promotion,
  Money,
  TrendCharts,
  Timer,
  Share,
  Setting,
  Document,
  ArrowRight,
  Plus,
  Clock,
  VideoCamera,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

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
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '退出确认',
      {
        confirmButtonText: '确定退出',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await authStore.logout()
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}
</script>

<style scoped>
/* 仪表盘容器 */
.dashboard {
  background: var(--bg-primary);
  min-height: 100vh;
  padding: var(--space-md);
}

/* 顶部工具栏 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
  padding: var(--space-lg) var(--space-xl);
  background: linear-gradient(135deg, var(--bg-secondary), rgba(99, 102, 241, 0.02));
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  position: relative;
  overflow: hidden;
}


.welcome-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.header-left .dashboard-title {
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
}

.welcome-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.secondary-btn {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-sm) var(--space-lg);
  font-weight: 600;
  color: var(--text-primary);
  transition: all var(--transition-base);
}

.secondary-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

.primary-btn {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  border-radius: var(--radius-lg);
  padding: var(--space-sm) var(--space-lg);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
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

/* 快速操作入口 */
.quick-actions {
  margin-bottom: var(--space-xl);
}

.quick-actions .section-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.quick-actions .section-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.quick-actions .section-header p {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
}

.action-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: var(--space-lg);
}

.quick-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-xl) var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.quick-action:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-color);
}

.quick-action:hover .action-arrow {
  transform: translateX(4px);
}

.primary-action {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: white;
  border: none;
  grid-row: span 2;
  box-shadow: var(--shadow-md);
}

.primary-action:hover {
  box-shadow: 0 12px 35px rgba(99, 102, 241, 0.4);
  transform: translateY(-6px);
}

.action-icon-large {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  margin-bottom: var(--space-lg);
  position: relative;
  z-index: 2;
  backdrop-filter: blur(10px);
}

.action-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: white;
  margin-bottom: var(--space-md);
  position: relative;
  z-index: 2;
  box-shadow: var(--shadow-sm);
}

.primary-action .action-icon {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.action-content h3 {
  font-size: var(--text-xl);
  font-weight: 700;
  margin: 0 0 var(--space-xs) 0;
  color: var(--text-primary);
  position: relative;
  z-index: 2;
}

.primary-action .action-content h3 {
  color: white;
}

.action-content h4 {
  font-size: var(--text-lg);
  font-weight: 600;
  margin: 0 0 var(--space-xs) 0;
  color: var(--text-primary);
  position: relative;
  z-index: 2;
}

.action-content p {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  position: relative;
  z-index: 2;
}

.primary-action .action-content p {
  color: rgba(255, 255, 255, 0.9);
}

.action-badge {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  background: rgba(255, 255, 255, 0.25);
  color: white;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  backdrop-filter: blur(10px);
  z-index: 2;
}

.action-arrow {
  position: absolute;
  bottom: var(--space-md);
  right: var(--space-md);
  color: var(--primary-color);
  transition: all var(--transition-base);
  z-index: 2;
}

.action-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 1;
}

.primary-action:hover .action-glow {
  opacity: 1;
}

/* 主要内容区 */
.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xl);
}

/* 统计行 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.mini-stat {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.mini-stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: var(--space-md);
}

.mini-stat-icon.projects {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.mini-stat-icon.tasks {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.mini-stat-icon.videos {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.mini-stat-icon.cost {
  background: linear-gradient(135deg, #fa709a, #fee140);
}

.mini-stat-info {
  flex: 1;
}

.mini-stat-number {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.mini-stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

/* 区块样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.recent-projects,
.task-queue,
.recent-activity {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

/* 空状态样式 */
.empty-projects,
.empty-queue,
.empty-activity {
  text-align: center;
  padding: var(--space-2xl) var(--space-lg);
  color: var(--text-secondary);
}

.empty-projects .el-icon,
.empty-queue .el-icon,
.empty-activity .el-icon {
  color: var(--text-tertiary);
  opacity: 0.6;
  margin-bottom: var(--space-md);
}

.empty-projects p,
.empty-queue p,
.empty-activity p {
  margin: 0 0 var(--space-md) 0;
  font-size: var(--text-base);
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: var(--space-4xl) var(--space-2xl);
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: var(--space-2xl);
  color: var(--text-tertiary);
  opacity: 0.6;
}

.empty-state h4 {
  margin: 0 0 var(--space-md) 0;
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 var(--space-xl) 0;
  font-size: var(--text-base);
}

.empty-state .el-button {
  padding: var(--space-md) var(--space-2xl);
  font-weight: 600;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.empty-state .el-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255,255,255,0.2),
    transparent
  );
  transition: left var(--transition-base);
}

.empty-state .el-button:hover::before {
  left: 100%;
}

/* 用户欢迎区域 */
.user-welcome {
  display: flex;
  align-items: center;
}

.user-welcome .el-avatar {
  box-shadow: var(--shadow-lg);
  border: 3px solid var(--bg-primary);
  position: relative;
}

.user-welcome .el-avatar::before {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
  border-radius: var(--radius-full);
  z-index: -1;
  opacity: 0.8;
}

/* 动画 */
@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 新的响应式设计 */
@media (max-width: 1200px) {
  .action-grid {
    grid-template-columns: 1fr 1fr 1fr 1fr;
  }

  .primary-action {
    grid-row: span 1;
  }
}

@media (max-width: 968px) {
  .dashboard {
    padding: var(--space-sm);
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
    padding: var(--space-md);
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .action-grid {
    grid-template-columns: 1fr 1fr;
  }

  .main-content {
    grid-template-columns: 1fr;
    gap: var(--space-lg);
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: var(--space-xs);
  }

  .dashboard-title {
    font-size: var(--text-xl) !important;
  }

  .title-icon {
    width: 20px !important;
    height: 20px !important;
  }

  .create-btn {
    padding: var(--space-sm) var(--space-md);
    font-size: var(--text-sm);
  }

  .username {
    display: none;
  }

  .action-grid {
    grid-template-columns: 1fr;
    gap: var(--space-md);
  }

  .quick-action {
    padding: var(--space-lg) var(--space-md);
  }

  .action-icon-large {
    width: 48px;
    height: 48px;
  }

  .action-icon {
    width: 40px;
    height: 40px;
  }

  .action-content h3 {
    font-size: var(--text-base);
  }

  .action-content h4 {
    font-size: var(--text-sm);
  }

  .action-content p {
    font-size: var(--text-xs);
  }

  .stats-row {
    grid-template-columns: 1fr;
    gap: var(--space-sm);
  }

  .mini-stat {
    padding: var(--space-sm);
  }

  .mini-stat-icon {
    width: 32px;
    height: 32px;
  }

  .mini-stat-number {
    font-size: var(--text-lg);
  }

  .section-header h3 {
    font-size: var(--text-base);
  }

  .recent-projects,
  .task-queue,
  .recent-activity {
    padding: var(--space-md);
    margin-bottom: var(--space-md);
  }

  .empty-projects,
  .empty-queue,
  .empty-activity {
    padding: var(--space-lg) var(--space-md);
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: var(--space-xs);
  }

  .dashboard-header {
    padding: var(--space-sm);
  }

  .action-grid {
    grid-template-columns: 1fr;
  }

  .quick-action {
    padding: var(--space-md);
  }

  .action-icon-large,
  .action-icon {
    width: 36px;
    height: 36px;
  }

  .stats-row {
    margin-bottom: var(--space-lg);
  }

  .recent-projects,
  .task-queue,
  .recent-activity {
    padding: var(--space-sm);
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

.quick-action {
  animation: slide-up 0.5s ease-out;
}

.quick-action:nth-child(1) {
  animation-delay: 0.1s;
}

.quick-action:nth-child(2) {
  animation-delay: 0.2s;
}

.quick-action:nth-child(3) {
  animation-delay: 0.3s;
}

.quick-action:nth-child(4) {
  animation-delay: 0.4s;
}

.mini-stat {
  animation: slide-up 0.6s ease-out;
}

.mini-stat:nth-child(1) {
  animation-delay: 0.5s;
}

.mini-stat:nth-child(2) {
  animation-delay: 0.6s;
}

.mini-stat:nth-child(3) {
  animation-delay: 0.7s;
}

.mini-stat:nth-child(4) {
  animation-delay: 0.8s;
}

.recent-projects,
.task-queue,
.recent-activity {
  animation: slide-up 0.7s ease-out;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .stat-card,
  .action-item {
    background: var(--bg-dark);
    border-color: var(--gray-700);
  }

  .action-item:hover {
    background: var(--gray-800);
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .stat-card,
  .action-item {
    border-width: 2px;
  }

  .stat-card:hover,
  .action-item:hover {
    border-width: 3px;
  }
}

/* 现代化渐变背景 */
.modern-gradient-1 {
  position: relative;
}

.modern-gradient-1::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%);
  border-radius: var(--radius-2xl);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 0;
}

.modern-gradient-1:hover::after {
  opacity: 1;
}

.modern-gradient-2::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(240, 147, 251, 0.05) 0%,
    rgba(245, 87, 108, 0.05) 100%);
  border-radius: var(--radius-2xl);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 0;
}

.modern-gradient-2:hover::after {
  opacity: 1;
}

.modern-gradient-3::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(79, 172, 254, 0.05) 0%,
    rgba(0, 242, 254, 0.05) 100%);
  border-radius: var(--radius-2xl);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 0;
}

.modern-gradient-3:hover::after {
  opacity: 1;
}

.modern-gradient-4::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(250, 112, 154, 0.05) 0%,
    rgba(254, 225, 64, 0.05) 100%);
  border-radius: var(--radius-2xl);
  opacity: 0;
  transition: opacity var(--transition-base);
  z-index: 0;
}

.modern-gradient-4:hover::after {
  opacity: 1;
}

/* 脉冲动画 */
.stat-card:hover .stat-card-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: var(--shadow-md);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
  }
}

/* 数字跳动动画 */
.stat-card:hover .stat-number {
  animation: bounce 1s ease-in-out;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-5px);
  }
  60% {
    transform: translateY(-3px);
  }
}

/* 磁性边框效果 */
.stat-card {
  position: relative;
  z-index: 1;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg,
    var(--primary-color),
    var(--secondary-color),
    var(--success-color),
    var(--warning-color));
  border-radius: var(--radius-2xl);
  z-index: -1;
  opacity: 0;
  transition: opacity var(--transition-base);
  animation: border-rotate 3s linear infinite;
}

@keyframes border-rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.stat-card:hover::before {
  opacity: 1;
}

/* 3D变换效果 */
.stat-card {
  transform-style: preserve-3d;
  transition: transform var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-8px) rotateX(5deg);
}

/* 浮动粒子效果 */
.stat-card::after {
  content: '';
  position: absolute;
  top: 10%;
  left: 10%;
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  animation: float-particle 3s ease-in-out infinite;
  opacity: 0;
  transition: opacity var(--transition-base);
}

.stat-card:hover::after {
  opacity: 1;
}

@keyframes float-particle {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.8;
  }
  33% {
    transform: translate(30px, -30px) scale(0.5);
    opacity: 0.4;
  }
  66% {
    transform: translate(-20px, 20px) scale(1.5);
    opacity: 0.6;
  }
}

/* 响应式增强 */
@media (max-width: 768px) {
  .stat-card:hover {
    transform: translateY(-4px);
  }

  .stat-card:hover .stat-card-icon {
    animation: none;
  }

  .stat-card:hover .stat-number {
    animation: none;
  }
}

/* 减少动画偏好支持 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>