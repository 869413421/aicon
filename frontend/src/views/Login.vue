<template>
  <div class="login-form">
    <!-- 表单标题 -->
    <div class="form-header">
      <el-icon class="header-icon"><User /></el-icon>
      <h2>账户登录</h2>
    </div>

    <!-- 登录表单 -->
    <el-form
      ref="loginFormRef"
      :model="loginForm"
      :rules="loginRules"
      @submit.prevent="handleLogin"
      label-position="top"
      size="large"
      class="login-form-content"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="loginForm.username"
          placeholder="请输入用户名"
          :prefix-icon="User"
          clearable
          @keyup.enter="handleLogin"
        />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
          :prefix-icon="Lock"
          show-password
          clearable
          @keyup.enter="handleLogin"
        />
      </el-form-item>

      <el-form-item class="submit-item">
        <el-button
          type="primary"
          size="large"
          :loading="authStore.loading"
          @click="handleLogin"
          class="submit-button"
        >
          <span v-if="!authStore.loading">登录</span>
          <span v-else>登录中...</span>
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 底部链接 -->
    <div class="form-footer">
      <p>还没有账户？
        <router-link to="/register" class="link">
          立即注册
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref()

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应为3-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度应为6-128个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()

    await authStore.login(loginForm)

    ElMessage.success('登录成功')

    // Redirect to the intended page or dashboard
    const redirect = router.currentRoute.value.query.redirect || '/dashboard'
    router.push(redirect)

  } catch (error) {
    // Error is handled by the auth store
    console.error('登录失败:', error)
  }
}
</script>

<style scoped>
.login-form {
  width: 100%;
  padding: 0;
}

/* 表单标题 */
.form-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
  text-align: center;
  justify-content: center;
}

.header-icon {
  font-size: 24px;
  color: var(--primary-color);
  padding: var(--space-sm);
  background: rgba(99, 102, 241, 0.1);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.form-header h2 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

/* 表单内容 */
.login-form-content {
  width: 100%;
}

.login-form-content :deep(.el-form-item) {
  margin-bottom: var(--space-lg);
}

.login-form-content :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
  font-size: var(--text-sm);
}

/* 输入框样式 */
:deep(.el-input__wrapper) {
  border-radius: var(--radius-lg);
  border: 2px solid var(--border-primary);
  background: var(--bg-secondary);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-lighter);
  box-shadow: var(--shadow-md);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

:deep(.el-input__inner) {
  font-size: var(--text-base);
  padding: var(--space-md) var(--space-lg);
  height: 48px;
}

:deep(.el-input__prefix-inner) {
  color: var(--text-tertiary);
}

/* 提交按钮项 */
.submit-item {
  margin-bottom: 0;
  margin-top: var(--space-xl);
}

.submit-button {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: var(--text-base);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 10px 25px rgba(99, 102, 241, 0.3);
}

.submit-button:active {
  transform: translateY(0);
}

/* 底部链接 */
.form-footer {
  text-align: center;
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-primary);
}

.form-footer p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.5;
}

.link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--transition-base);
  position: relative;
}

.link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--primary-color);
  transition: width var(--transition-base);
}

.link:hover {
  color: var(--primary-hover);
}

.link:hover::after {
  width: 100%;
}

/* 错误状态动画 */
:deep(.el-form-item.is-error .el-input__wrapper) {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 加载状态 */
:deep(.el-button.is-loading) {
  pointer-events: none;
}

:deep(.el-loading-spinner) {
  margin-right: var(--space-sm);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-header {
    margin-bottom: var(--space-lg);
  }

  .form-header h2 {
    font-size: var(--text-lg);
  }

  .header-icon {
    font-size: 20px;
    padding: var(--space-sm);
  }

  :deep(.el-input__inner) {
    height: 44px;
    padding: var(--space-sm) var(--space-md);
  }

  .submit-button {
    height: 44px;
  }
}

@media (max-width: 480px) {
  .form-header {
    flex-direction: column;
    gap: var(--space-sm);
    text-align: center;
  }

  .form-header h2 {
    font-size: var(--text-base);
  }

  .header-icon {
    font-size: 18px;
    padding: var(--space-xs);
  }

  :deep(.el-input__inner) {
    height: 40px;
  }

  .submit-button {
    height: 40px;
    font-size: var(--text-sm);
  }
}
</style>