<template>
  <div class="settings-page">
    <div class="settings-header">
      <div class="header-content">
        <el-button
          type="text"
          @click="$router.push('/dashboard')"
          class="back-button"
          :icon="ArrowLeft"
        >
          返回仪表板
        </el-button>
        <div class="header-text">
          <h1>系统设置</h1>
          <p>管理您的账户和应用程序设置</p>
        </div>
      </div>
    </div>

    <div class="settings-content">
      <el-row :gutter="24">
        <el-col :span="8">
          <div class="settings-menu">
            <el-menu
              :default-active="activeTab"
              mode="vertical"
              @select="handleMenuSelect"
              class="settings-nav"
            >
              <el-menu-item index="profile">
                <el-icon><User /></el-icon>
                <span>个人资料</span>
              </el-menu-item>
              <el-menu-item index="account">
                <el-icon><Lock /></el-icon>
                <span>账户安全</span>
              </el-menu-item>
              <el-menu-item index="preferences">
                <el-icon><Setting /></el-icon>
                <span>偏好设置</span>
              </el-menu-item>
            </el-menu>
          </div>
        </el-col>

        <el-col :span="16">
          <div class="settings-panel">
            <!-- 个人资料 -->
            <div v-show="activeTab === 'profile'" class="setting-section">
              <h2>个人资料</h2>
              <p>管理您的个人信息和头像</p>

              <div class="profile-section">
                <div class="avatar-section">
                  <div class="avatar-container" @click="triggerFileSelect" :class="{ 'uploading': isUploadingAvatar }">
                    <el-avatar :size="80" :src="previewAvatar || userForm.avatar_url" class="user-avatar">
                      <el-icon size="40"><User /></el-icon>
                    </el-avatar>
                    <div v-if="isUploadingAvatar" class="upload-overlay">
                      <el-progress type="circle" :percentage="uploadProgress" :width="60" />
                    </div>
                    <div v-else class="avatar-hover-overlay">
                      <el-icon><Camera /></el-icon>
                      <span>点击更换头像</span>
                    </div>
                  </div>
                  <div class="avatar-actions">
                    <input
                      ref="avatarFileInput"
                      type="file"
                      accept="image/jpeg,image/jpg,image/png"
                      style="display: none"
                      @change="handleAvatarSelect"
                    />
                    <el-button
                      type="primary"
                      plain
                      @click="triggerFileSelect"
                      :loading="isUploadingAvatar"
                      :disabled="isUploadingAvatar"
                    >
                      {{ isUploadingAvatar ? '上传中...' : '更换头像' }}
                    </el-button>
                    <el-button
                      v-if="previewAvatar || userForm.avatar_url"
                      type="danger"
                      plain
                      size="small"
                      @click="removeAvatar"
                      :disabled="isUploadingAvatar"
                    >
                      移除头像
                    </el-button>
                    <p class="upload-tip">支持 JPG、PNG 格式，建议尺寸 200x200px，最大5MB</p>
                  </div>
                </div>

                <el-form :model="userForm" label-width="120px" class="profile-form">
                  <el-form-item label="用户名">
                    <el-input v-model="userForm.username" disabled>
                      <template #prefix>
                        <el-icon><User /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>

                  <el-form-item label="显示名称">
                    <el-input
                      v-model="userForm.display_name"
                      placeholder="请输入显示名称"
                      maxlength="50"
                      show-word-limit
                    >
                      <template #prefix>
                        <el-icon><User /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>

                  <el-form-item label="邮箱地址">
                    <el-input v-model="userForm.email" disabled>
                      <template #prefix>
                        <el-icon><Message /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>

                  <el-form-item label="注册时间">
                    <el-input :value="formatDate(userForm.created_at, {}, userTimezone)" disabled>
                      <template #prefix>
                        <el-icon><Clock /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>

                  <el-form-item>
                    <el-button
                      type="primary"
                      @click="saveProfile"
                      :loading="profileLoading"
                    >
                      保存更改
                    </el-button>
                    <el-button @click="resetProfileForm">重置</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 账户安全 -->
            <div v-show="activeTab === 'account'" class="setting-section">
              <h2>账户安全</h2>
              <p>保护您的账户安全</p>

              <div class="security-sections">
                <div class="security-card">
                  <div class="card-header">
                    <div class="card-icon">
                      <el-icon><Lock /></el-icon>
                    </div>
                    <div class="card-content">
                      <h3>修改密码</h3>
                      <p>定期更改密码以保护账户安全</p>
                    </div>
                  </div>
                  <el-button @click="showPasswordDialog = true" type="primary">
                    修改密码
                  </el-button>
                </div>

                <div class="security-card">
                  <div class="card-header">
                    <div class="card-icon shield">
                      <el-icon><Key /></el-icon>
                    </div>
                    <div class="card-content">
                      <h3>账户状态</h3>
                      <p>
                        <el-tag type="success" size="small">安全</el-tag>
                        上次登录：{{ formatDate(authStore.user?.last_login, {}, userTimezone) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 偏好设置 -->
            <div v-show="activeTab === 'preferences'" class="setting-section">
              <h2>偏好设置</h2>
              <p>自定义应用程序的外观和行为</p>

              <el-form :model="preferencesForm" label-width="120px" class="preferences-form">
                <el-form-item label="主题模式">
                  <el-radio-group v-model="preferencesForm.theme" @change="savePreferences">
                    <el-radio label="light">
                      <div class="preference-option">
                        <el-icon><Sunny /></el-icon>
                        <span>浅色模式</span>
                      </div>
                    </el-radio>
                    <el-radio label="dark">
                      <div class="preference-option">
                        <el-icon><Moon /></el-icon>
                        <span>深色模式</span>
                      </div>
                    </el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="界面语言">
                  <el-select
                    v-model="preferencesForm.language"
                    placeholder="选择界面语言"
                    @change="savePreferences"
                  >
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>

                <el-form-item label="时区">
                  <el-select
                    v-model="preferencesForm.timezone"
                    placeholder="选择时区"
                    @change="savePreferences"
                  >
                    <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                    <el-option label="UTC" value="UTC" />
                    <el-option label="America/New_York" value="America/New_York" />
                    <el-option label="Europe/London" value="Europe/London" />
                  </el-select>
                </el-form-item>

                <el-form-item label="自动保存">
                  <el-switch
                    v-model="preferencesForm.autoSave"
                    @change="savePreferences"
                  />
                  <span class="setting-description">自动保存您的编辑内容</span>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      width="520px"
      :close-on-click-modal="false"
      class="password-dialog"
      :show-close="true"
    >
      <template #header>
        <div class="password-dialog-header compact">
          <div class="dialog-icon">
            <el-icon size="28"><Lock /></el-icon>
          </div>
          <div class="dialog-title">
            <h3>修改密码</h3>
            <p>设置新的安全密码</p>
          </div>
        </div>
      </template>

      <div class="password-form-container compact">
        <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-position="top">
          <div class="form-group compact">
            <el-form-item prop="current">
              <el-input
                v-model="passwordForm.current"
                type="password"
                placeholder="当前密码"
                size="default"
                show-password
                clearable
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <div class="form-group compact">
            <el-form-item prop="new">
              <el-input
                v-model="passwordForm.new"
                type="password"
                placeholder="新密码"
                size="default"
                show-password
                clearable
                @input="checkPasswordStrength"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>

              <!-- 紧凑的密码强度指示器和要求 -->
              <div class="compact-password-info" v-if="passwordForm.new">
                <!-- 密码强度条 -->
                <div class="compact-strength">
                  <div class="strength-label">
                    <span>强度：</span>
                    <span :class="getPasswordStrengthClass()">{{ getPasswordStrengthText() }}</span>
                  </div>
                  <div class="strength-bar">
                    <div class="strength-fill" :class="getPasswordStrengthClass()" :style="getPasswordStrengthWidth()"></div>
                  </div>
                </div>

                <!-- 紧凑的密码要求 -->
                <div class="compact-requirements">
                  <div class="requirement-row">
                    <div class="requirement-item" :class="{ 'satisfied': passwordForm.new.length >= 8 }">
                      <el-icon size="12"><Check v-if="passwordForm.new.length >= 8" /><Close v-else /></el-icon>
                      <span>8位+</span>
                    </div>
                    <div class="requirement-item" :class="{ 'satisfied': /[A-Z]/.test(passwordForm.new) }">
                      <el-icon size="12"><Check v-if="/[A-Z]/.test(passwordForm.new)" /><Close v-else /></el-icon>
                      <span>大写</span>
                    </div>
                    <div class="requirement-item" :class="{ 'satisfied': /[a-z]/.test(passwordForm.new) }">
                      <el-icon size="12"><Check v-if="/[a-z]/.test(passwordForm.new)" /><Close v-else /></el-icon>
                      <span>小写</span>
                    </div>
                  </div>
                  <div class="requirement-row">
                    <div class="requirement-item" :class="{ 'satisfied': /\d/.test(passwordForm.new) }">
                      <el-icon size="12"><Check v-if="/\d/.test(passwordForm.new)" /><Close v-else /></el-icon>
                      <span>数字</span>
                    </div>
                    <div class="requirement-item" :class="{ 'satisfied': hasSpecialCharacter }">
                      <el-icon size="12"><Check v-if="hasSpecialCharacter" /><Close v-else /></el-icon>
                      <span>特殊字符</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-form-item>
          </div>

          <div class="form-group compact">
            <el-form-item prop="confirm">
              <el-input
                v-model="passwordForm.confirm"
                type="password"
                placeholder="确认新密码"
                size="default"
                show-password
                clearable
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>

              <!-- 紧凑的密码匹配状态 -->
              <div class="compact-match" v-if="passwordForm.confirm">
                <div class="match-item" :class="{ 'matched': passwordForm.new === passwordForm.confirm }">
                  <el-icon size="14"><Check v-if="passwordForm.new === passwordForm.confirm" /><Close v-else /></el-icon>
                  <span>密码匹配</span>
                </div>
              </div>
            </el-form-item>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="password-dialog-footer compact">
          <el-button @click="closePasswordDialog">取消</el-button>
          <el-button
            type="primary"
            @click="changePassword"
            :loading="passwordLoading"
            :disabled="!isFormValid"
          >
            {{ passwordLoading ? '修改中...' : '确认修改' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  User,
  Lock,
  Setting,
  Message,
  Clock,
  Sunny,
  Moon,
  Camera,
  ArrowLeft,
  Key,
  Check,
  Close
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate, getUserTimezone } from '@/utils/dateUtils'

const authStore = useAuthStore()
const activeTab = ref('profile')
const showPasswordDialog = ref(false)
const profileLoading = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)

// 密码强度相关
const passwordStrength = ref(0)

// 头像上传相关
const avatarFileInput = ref(null)
const isUploadingAvatar = ref(false)
const uploadProgress = ref(0)
const previewAvatar = ref('')

// 用户表单数据
const userForm = reactive({
  username: '',
  display_name: '',
  email: '',
  avatar_url: '',
  created_at: new Date().toISOString()
})

// 密码修改表单
const passwordForm = reactive({
  current: '',
  new: '',
  confirm: ''
})

// 偏好设置表单
const preferencesForm = reactive({
  theme: 'light',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  autoSave: true
})

// 密码验证规则
const passwordRules = {
  current: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback()
          return
        }
        if (!/[A-Z]/.test(value)) {
          callback(new Error('密码必须包含大写字母'))
          return
        }
        if (!/[a-z]/.test(value)) {
          callback(new Error('密码必须包含小写字母'))
          return
        }
        if (!/\d/.test(value)) {
          callback(new Error('密码必须包含数字'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// 密码强度检查
const checkPasswordStrength = () => {
  let strength = 0
  const password = passwordForm.new

  if (!password) {
    passwordStrength.value = 0
    return
  }

  // 长度检查
  if (password.length >= 8) strength += 1
  if (password.length >= 12) strength += 1

  // 字符类型检查
  if (/[a-z]/.test(password)) strength += 1  // 小写字母
  if (/[A-Z]/.test(password)) strength += 1  // 大写字母
  if (/\d/.test(password)) strength += 1      // 数字
  if (/[!@#$%^&*()\-_+=.,?":{}|<>]/.test(password)) strength += 1  // 特殊字符

  passwordStrength.value = Math.min(strength, 5)
}

// 密码强度文本
const getPasswordStrengthText = () => {
  if (passwordStrength.value <= 2) return '弱'
  if (passwordStrength.value <= 4) return '中等'
  return '强'
}

// 密码强度样式类
const getPasswordStrengthClass = () => {
  if (passwordStrength.value <= 2) return 'weak'
  if (passwordStrength.value <= 4) return 'medium'
  return 'strong'
}

// 密码强度进度条宽度
const getPasswordStrengthWidth = () => {
  return { width: `${(passwordStrength.value / 5) * 100}%` }
}

// 是否包含特殊字符
const hasSpecialCharacter = computed(() => {
  if (!passwordForm.new) return false
  const specialChars = /[!@#$%^&*()\-_+=.,?":{}|<>]/
  return specialChars.test(passwordForm.new)
})

// 表单是否有效
const isFormValid = computed(() => {
  return passwordForm.current &&
         passwordForm.new &&
         passwordForm.confirm &&
         passwordForm.new === passwordForm.confirm &&
         passwordForm.new.length >= 8 &&
         /[A-Z]/.test(passwordForm.new) &&
         /[a-z]/.test(passwordForm.new) &&
         /\d/.test(passwordForm.new)
})

// 用户时区
const userTimezone = computed(() => {
  return getUserTimezone(authStore.user);
})

// 关闭密码对话框
const closePasswordDialog = () => {
  showPasswordDialog.value = false
  // 重置表单
  Object.assign(passwordForm, {
    current: '',
    new: '',
    confirm: ''
  })
  passwordStrength.value = 0
}

// 菜单选择处理
const handleMenuSelect = (index) => {
  activeTab.value = index
}

// 初始化用户数据
const initUserData = async () => {
  try {
    if (authStore.user) {
      userForm.username = authStore.user.username || ''
      userForm.display_name = authStore.user.display_name || ''
      userForm.email = authStore.user.email || ''
      userForm.avatar_url = authStore.user.avatar_url || ''
      userForm.created_at = authStore.user.created_at || new Date().toISOString()
    } else {
      // 如果没有用户信息，尝试获取
      await authStore.getCurrentUser()
      initUserData()
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 保存个人资料
const saveProfile = async () => {
  if (!userForm.display_name.trim()) {
    ElMessage.warning('请输入显示名称')
    return
  }

  profileLoading.value = true
  try {
    const updateData = {
      display_name: userForm.display_name.trim()
    }

    await authStore.updateProfile(updateData)
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    console.error('更新个人资料失败:', error)
    ElMessage.error('更新个人资料失败，请重试')
  } finally {
    profileLoading.value = false
  }
}

// 重置个人资料表单
const resetProfileForm = () => {
  initUserData()
  ElMessage.info('表单已重置')
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  passwordLoading.value = true
  try {
    await authStore.changePassword({
      current_password: passwordForm.current,
      new_password: passwordForm.new
    })

    showPasswordDialog.value = false
    ElMessage.success('密码修改成功')

    // 重置表单
    Object.assign(passwordForm, {
      current: '',
      new: '',
      confirm: ''
    })
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('修改密码失败，请检查当前密码是否正确')
  } finally {
    passwordLoading.value = false
  }
}

// 保存偏好设置
const savePreferences = async () => {
  try {
    // 保存到后端服务器
    const updateData = {
      preferences: {
        theme: preferencesForm.theme,
        autoSave: preferencesForm.autoSave
      },
      timezone: preferencesForm.timezone,
      language: preferencesForm.language
    }

    await authStore.updateProfile(updateData)

    // 应用主题设置到前端
    applyTheme(preferencesForm.theme)

    ElMessage.success('偏好设置已保存')
  } catch (error) {
    console.error('保存偏好设置失败:', error)
    ElMessage.error('保存偏好设置失败，请重试')
  }
}

// 应用主题设置
const applyTheme = (theme) => {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 加载偏好设置
const loadPreferences = async () => {
  try {
    // 从后端用户数据加载偏好设置
    if (authStore.user) {
      // 加载preferences字段
      if (authStore.user.preferences) {
        preferencesForm.theme = authStore.user.preferences.theme || 'light'
        preferencesForm.autoSave = authStore.user.preferences.autoSave !== undefined ? authStore.user.preferences.autoSave : true
      }

      // 加载language和timezone字段
      preferencesForm.language = authStore.user.language || 'zh-CN'
      preferencesForm.timezone = authStore.user.timezone || 'Asia/Shanghai'

      // 应用主题设置到前端
      applyTheme(preferencesForm.theme)
    }
  } catch (error) {
    console.error('加载偏好设置失败:', error)
    // 如果从后端加载失败，使用默认值
    preferencesForm.theme = 'light'
    preferencesForm.language = 'zh-CN'
    preferencesForm.timezone = 'Asia/Shanghai'
    preferencesForm.autoSave = true

    // 应用默认主题
    applyTheme(preferencesForm.theme)
  }
}

// 触发文件选择
const triggerFileSelect = () => {
  if (isUploadingAvatar.value) return
  avatarFileInput.value?.click()
}

// 处理头像选择
const handleAvatarSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型
  if (!file.type.match(/^image\/(jpeg|jpg|png)$/)) {
    ElMessage.error('请选择 JPG 或 PNG 格式的图片文件')
    return
  }

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片文件大小不能超过 5MB')
    return
  }

  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    previewAvatar.value = e.target.result
  }
  reader.readAsDataURL(file)

  // 开始上传
  uploadAvatar(file)
}

// 上传头像
const uploadAvatar = async (file) => {
  isUploadingAvatar.value = true
  uploadProgress.value = 0

  try {
    // 调用真实的上传API
    const response = await authStore.uploadAvatar(file, (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      )
      uploadProgress.value = percentCompleted
    })

    // 更新用户信息
    if (response.user) {
      Object.assign(userForm, {
        avatar_url: response.user.avatar_url
      })
    }

    ElMessage.success('头像上传成功！')

    // 清空预览和进度
    setTimeout(() => {
      previewAvatar.value = ''
      uploadProgress.value = 0
    }, 1000)

  } catch (error) {
    console.error('头像上传失败:', error)

    // 根据错误类型显示不同提示
    if (error.response?.status === 413) {
      ElMessage.error('图片文件过大，请选择小于5MB的图片')
    } else if (error.response?.status === 415) {
      ElMessage.error('不支持的图片格式，请选择JPG或PNG格式')
    } else if (error.response?.status === 400) {
      ElMessage.error(error.response?.data?.detail || '图片文件验证失败')
    } else {
      ElMessage.error('头像上传失败，请重试')
    }

    // 清空预览
    previewAvatar.value = ''
    uploadProgress.value = 0
  } finally {
    isUploadingAvatar.value = false
    // 清空文件输入
    if (avatarFileInput.value) {
      avatarFileInput.value.value = ''
    }
  }
}

// 移除头像
const removeAvatar = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要移除当前头像吗？',
      '确认操作',
      {
        confirmButtonText: '确定移除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // 调用真实的删除API
    const response = await authStore.removeAvatar()

    // 更新本地表单
    userForm.avatar_url = ''
    previewAvatar.value = ''

    ElMessage.success('头像已移除')
  } catch (error) {
    if (error === 'cancel') {
      return
    }

    console.error('移除头像失败:', error)

    if (error.response?.status === 400) {
      ElMessage.error(error.response?.data?.detail || '移除头像失败')
    } else {
      ElMessage.error('移除头像失败，请重试')
    }
  }
}

// 组件挂载时初始化数据
onMounted(async () => {
  await initUserData()
  await loadPreferences()
})
</script>

<style scoped>
.settings-page {
  padding: var(--space-xl);
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 100px);
}

.settings-header {
  margin-bottom: var(--space-2xl);
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
}

.back-button {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--transition-base);
  border-radius: var(--radius-lg);
}

.back-button:hover {
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.header-text {
  flex: 1;
}

.settings-header h1 {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.settings-header p {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin: 0;
}

.settings-content {
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.settings-menu {
  padding: var(--space-lg);
  background: linear-gradient(180deg, var(--bg-primary), var(--bg-secondary));
}

.settings-nav {
  border: none;
  background: transparent;
}

.settings-nav .el-menu-item {
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-xs);
  height: 56px;
  line-height: 56px;
  font-weight: 600;
  transition: all var(--transition-base);
}

.settings-nav .el-menu-item:hover {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  transform: translateX(4px);
}

.settings-nav .el-menu-item.is-active {
  background: var(--primary-color);
  color: white;
  box-shadow: var(--shadow-md);
}

.settings-panel {
  padding: var(--space-2xl);
  min-height: 500px;
}

.setting-section {
  margin-bottom: var(--space-2xl);
}

.setting-section h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.setting-section p {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-2xl) 0;
}

/* 个人资料样式 */
.profile-section {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-2xl);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
  padding: var(--space-lg);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
  border-radius: var(--radius-lg);
}

.avatar-container {
  position: relative;
  cursor: pointer;
  transition: all var(--transition-base);
}

.avatar-container:hover:not(.uploading) {
  transform: scale(1.05);
}

.avatar-container.uploading {
  cursor: not-allowed;
}

.user-avatar {
  box-shadow: var(--shadow-lg);
  border: 4px solid var(--bg-primary);
  transition: all var(--transition-base);
}

.avatar-container:hover .user-avatar:not(.uploading .user-avatar) {
  box-shadow: var(--shadow-xl);
  border-color: var(--primary-color);
}

.avatar-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity var(--transition-base);
  backdrop-filter: blur(2px);
}

.avatar-container:hover .avatar-hover-overlay {
  opacity: 1;
}

.avatar-hover-overlay .el-icon {
  font-size: 24px;
  margin-bottom: var(--space-xs);
}

.avatar-hover-overlay span {
  font-size: var(--text-xs);
  font-weight: 600;
}

.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.avatar-actions {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.upload-tip {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: var(--space-sm) 0 0 0;
  line-height: 1.5;
}

.profile-form {
  display: grid;
  gap: var(--space-lg);
}

/* 安全设置样式 */
.security-sections {
  display: grid;
  gap: var(--space-lg);
}

.security-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.security-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.security-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
  opacity: 0;
  transition: opacity var(--transition-base);
}

.security-card:hover::before {
  opacity: 1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-md);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  box-shadow: var(--shadow-md);
}

.card-icon.shield {
  background: linear-gradient(135deg, var(--success-color), #67c23a);
}

.card-content h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-xs) 0;
}

.card-content p {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* 偏好设置样式 */
.preferences-form {
  display: grid;
  gap: var(--space-xl);
}

.preference-option {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.setting-description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-left: var(--space-md);
}

/* 密码对话框样式 */
.password-dialog {
  border-radius: var(--radius-xl);
  overflow: hidden;
}

:deep(.password-dialog .el-dialog) {
  border-radius: var(--radius-xl);
  overflow: hidden;
}

:deep(.password-dialog .el-dialog__header) {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  padding: 0;
  border-radius: 0;
}

:deep(.password-dialog .el-dialog__headerbtn) {
  top: var(--space-lg);
  right: var(--space-lg);
  color: white;
}

:deep(.password-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

:deep(.password-dialog .el-dialog__body) {
  padding: 0;
}

:deep(.password-dialog .el-dialog__footer) {
  padding: var(--space-xl);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}

.password-dialog-header {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-xl);
  color: white;
}

/* 紧凑模式样式 */
.password-dialog-header.compact {
  padding: var(--space-lg) var(--space-xl);
}

.password-dialog-header.compact .dialog-icon {
  width: 48px;
  height: 48px;
}

.password-dialog-header.compact .dialog-title h3 {
  font-size: var(--text-xl);
}

.password-dialog-header.compact .dialog-title p {
  font-size: var(--text-sm);
}

.dialog-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.dialog-title h3 {
  font-size: var(--text-2xl);
  font-weight: 700;
  margin: 0 0 var(--space-xs) 0;
}

.dialog-title p {
  font-size: var(--text-base);
  opacity: 0.9;
  margin: 0;
}

.password-form-container {
  padding: var(--space-2xl);
  background: var(--bg-primary);
}

/* 紧凑表单容器 */
.password-form-container.compact {
  padding: var(--space-lg) var(--space-xl);
}

.form-group {
  margin-bottom: var(--space-2xl);
}

.form-group:last-child {
  margin-bottom: 0;
}

/* 紧凑表单组 */
.form-group.compact {
  margin-bottom: var(--space-lg);
}

.form-group-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.form-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.form-label {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* 紧凑密码信息样式 */
.compact-password-info {
  margin-top: var(--space-sm);
}

.compact-strength {
  margin-bottom: var(--space-sm);
}

.compact-strength .strength-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.compact-strength .strength-bar {
  height: 4px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

/* 紧凑密码要求 */
.compact-requirements {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  border: 1px solid var(--border-primary);
}

.requirement-row {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-xs);
}

.requirement-row:last-child {
  margin-bottom: 0;
}

.compact-requirements .requirement-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  flex: 1;
}

.compact-requirements .requirement-item.satisfied {
  color: var(--success-color);
}

.compact-requirements .requirement-item .el-icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.compact-requirements .requirement-item.satisfied .el-icon {
  background: var(--success-color);
  color: white;
}

/* 紧凑密码匹配状态 */
.compact-match {
  margin-top: var(--space-xs);
}

.compact-match .match-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.compact-match .match-item.matched {
  color: var(--success-color);
}

.compact-match .match-item .el-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.compact-match .match-item.matched .el-icon {
  background: var(--success-color);
  color: white;
}

/* 紧凑对话框底部 */
.password-dialog-footer.compact {
  padding: var(--space-lg) var(--space-xl);
  gap: var(--space-sm);
}

.password-dialog-footer.compact .el-button {
  min-width: 100px;
}

/* 密码强度指示器 */
.password-strength {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.strength-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.strength-label span:last-child {
  font-weight: 600;
}

.strength-label .weak {
  color: var(--danger-color);
}

.strength-label .medium {
  color: var(--warning-color);
}

.strength-label .strong {
  color: var(--success-color);
}

.strength-bar {
  height: 6px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
  background: var(--danger-color);
}

.strength-fill.medium {
  background: var(--warning-color);
}

.strength-fill.strong {
  background: var(--success-color);
}

/* 密码要求提示 */
.password-requirements {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.password-requirements h4 {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
}

.requirement-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  transition: all var(--transition-base);
}

.requirement-item.satisfied {
  color: var(--success-color);
}

.requirement-item .el-icon {
  font-size: 16px;
}

.requirement-item .el-icon:first-child {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.requirement-item.satisfied .el-icon:first-child {
  background: var(--success-color);
  color: white;
}

/* 密码匹配状态 */
.password-match {
  margin-top: var(--space-md);
}

.match-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  transition: all var(--transition-base);
}

.match-item.matched {
  color: var(--success-color);
}

.match-item .el-icon {
  font-size: 16px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.match-item.matched .el-icon {
  background: var(--success-color);
  color: white;
}

/* 对话框底部 */
.password-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  align-items: center;
}

.password-dialog-footer .el-button {
  min-width: 120px;
}

/* 表单样式增强 */
:deep(.password-dialog .el-form-item) {
  margin-bottom: 0;
}

:deep(.password-dialog .el-form-item__error) {
  font-size: var(--text-xs);
  color: var(--danger-color);
  margin-top: var(--space-xs);
}

/* 表单样式增强 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.el-input__wrapper) {
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all var(--transition-base);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

:deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

:deep(.el-button) {
  border-radius: var(--radius-lg);
  font-weight: 600;
  transition: all var(--transition-base);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  box-shadow: var(--shadow-sm);
}

:deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

:deep(.el-radio) {
  margin-right: 0;
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
}

:deep(.el-radio:hover) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

:deep(.el-radio.is-checked) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

:deep(.el-select .el-input__wrapper) {
  cursor: pointer;
}

:deep(.el-dialog) {
  border-radius: var(--radius-xl);
  overflow: hidden;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  padding: var(--space-xl);
}

:deep(.el-dialog__title) {
  font-size: var(--text-xl);
  font-weight: 700;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-page {
    padding: var(--space-md);
  }

  .settings-content {
    border-radius: var(--radius-lg);
  }

  .settings-panel {
    padding: var(--space-lg);
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .back-button {
    align-self: flex-start;
  }

  .avatar-section {
    flex-direction: column;
    text-align: center;
    gap: var(--space-lg);
  }

  .card-header {
    flex-direction: column;
    text-align: center;
    gap: var(--space-md);
  }

  .security-card {
    padding: var(--space-lg);
  }

  .preferences-form {
    gap: var(--space-lg);
  }

  .setting-section h2 {
    font-size: var(--text-xl);
    flex-direction: column;
    gap: var(--space-sm);
  }
}

@media (max-width: 480px) {
  .settings-page {
    padding: var(--space-sm);
  }

  .settings-header {
    margin-bottom: var(--space-lg);
  }

  .settings-header h1 {
    font-size: var(--text-2xl);
  }

  .settings-panel {
    padding: var(--space-md);
  }

  .avatar-section {
    padding: var(--space-md);
  }

  .profile-section {
    padding: var(--space-lg);
  }
}

/* 加载动画 */
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

.setting-section {
  animation: slide-up 0.6s ease-out;
}

.setting-section:nth-child(1) {
  animation-delay: 0.1s;
}

.setting-section:nth-child(2) {
  animation-delay: 0.2s;
}

.setting-section:nth-child(3) {
  animation-delay: 0.3s;
}

.security-card {
  animation: slide-up 0.6s ease-out;
}

.security-card:nth-child(1) {
  animation-delay: 0.4s;
}

.security-card:nth-child(2) {
  animation-delay: 0.5s;
}
</style>
