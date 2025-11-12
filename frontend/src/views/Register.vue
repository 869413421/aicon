<template>
  <div class="register-form">
    <!-- 表单标题 -->
    <div class="form-header">
      <el-icon class="header-icon"><User /></el-icon>
      <h2>创建账户</h2>
    </div>

    <!-- 注册表单 -->
    <el-form
      ref="registerFormRef"
      :model="registerForm"
      :rules="registerRules"
      @submit.prevent="handleRegister"
      label-position="top"
      size="large"
      class="register-form-content"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="registerForm.username"
          placeholder="请输入用户名"
          :prefix-icon="User"
          clearable
        />
      </el-form-item>

      <el-form-item label="邮箱地址" prop="email">
        <el-input
          v-model="registerForm.email"
          type="email"
          placeholder="请输入邮箱地址"
          :prefix-icon="Message"
          clearable
        />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input
          v-model="registerForm.password"
          type="password"
          placeholder="请输入密码"
          :prefix-icon="Lock"
          show-password
          clearable
        />
      </el-form-item>

      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input
          v-model="registerForm.confirmPassword"
          type="password"
          placeholder="请再次输入密码"
          :prefix-icon="Lock"
          show-password
          clearable
          @keyup.enter="handleRegister"
        />
      </el-form-item>

      <el-form-item class="submit-item">
        <el-button
          type="primary"
          size="large"
          :loading="authStore.loading"
          @click="handleRegister"
          class="submit-button"
        >
          <span v-if="!authStore.loading">注册</span>
          <span v-else>注册中...</span>
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 底部链接 -->
    <div class="form-footer">
      <p>已有账户？
        <router-link to="/login" class="link">
          立即登录
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const registerFormRef = ref()

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应为3-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度应为8-128个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()

    await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })

    ElMessage.success('注册成功！请登录您的账户。')

    // Redirect to login page
    router.push('/login')

  } catch (error) {
    // Error is handled by the auth store
    console.error('注册失败:', error)
  }
}
</script>

<style scoped>
.register-form {
  width: 100%;
  padding: 0;
}

/* 表单标题 */
.form-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
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
.register-form-content {
  width: 100%;
}

.register-form-content :deep(.el-form-item) {
  margin-bottom: var(--space-md);
}

.register-form-content :deep(.el-form-item__label) {
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
  padding: var(--space-sm) var(--space-md);
  height: 44px;
}

:deep(.el-input__prefix-inner) {
  color: var(--text-tertiary);
}

/* 提交按钮项 */
.submit-item {
  margin-bottom: 0;
  margin-top: var(--space-lg);
}

.submit-button {
  width: 100%;
  height: 44px;
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
    margin-bottom: var(--space-md);
  }

  .form-header h2 {
    font-size: var(--text-lg);
  }

  .header-icon {
    font-size: 20px;
    padding: var(--space-sm);
  }

  .register-form-content :deep(.el-form-item) {
    margin-bottom: var(--space-sm);
  }

  :deep(.el-input__inner) {
    height: 40px;
    padding: var(--space-sm) var(--space-md);
  }

  .submit-button {
    height: 40px;
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
    height: 38px;
    padding: var(--space-xs) var(--space-sm);
    font-size: var(--text-sm);
  }

  .submit-button {
    height: 38px;
    font-size: var(--text-sm);
  }

  .register-form-content :deep(.el-form-item) {
    margin-bottom: var(--space-xs);
  }
}

/* 注册表单特殊优化 - 字段较多时减小间距 */
@media (min-height: 800px) {
  .register-form-content :deep(.el-form-item) {
    margin-bottom: var(--space-md);
  }
}

@media (max-height: 700px) {
  .register-form-content :deep(.el-form-item) {
    margin-bottom: var(--space-sm);
  }

  .form-header {
    margin-bottom: var(--space-md);
  }

  .submit-item {
    margin-top: var(--space-md);
  }
}
</style>