import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  // 登录
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await authService.login(credentials)
      token.value = response.access_token
      localStorage.setItem('token', token.value)
      await getCurrentUser()
      return response
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (userData) => {
    loading.value = true
    try {
      const response = await authService.register(userData)
      return response
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    if (!token.value) return

    try {
      const user_data = await authService.getCurrentUser()
      user.value = user_data
      return user_data
    } catch (error) {
      logout()
      throw error
    }
  }

  // 更新用户信息
  const updateProfile = async (userData) => {
    const updated_user = await authService.updateProfile(userData)
    user.value = updated_user
    return updated_user
  }

  // 修改密码
  const changePassword = async (passwordData) => {
    await authService.changePassword(passwordData)
  }

  // 获取用户统计信息
  const getUserStats = async () => {
    return await authService.getUserStats()
  }

  // 重新发送验证邮件
  const resendVerificationEmail = async () => {
    return await authService.resendVerificationEmail()
  }

  // 删除账户
  const deleteAccount = async (password) => {
    return await authService.deleteAccount(password)
  }

  // 上传头像
  const uploadAvatar = async (file) => {
    const response = await authService.uploadAvatar(file)
    if (response.user) {
      user.value = response.user
    }
    return response
  }

  // 删除头像
  const removeAvatar = async () => {
    const response = await authService.deleteAvatar()
    if (response.user) {
      user.value = response.user
    }
    return response
  }

  // 获取头像信息
  const getAvatarInfo = async () => {
    return await authService.getAvatarInfo()
  }

  // 登出
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    login,
    register,
    getCurrentUser,
    updateProfile,
    changePassword,
    getUserStats,
    resendVerificationEmail,
    deleteAccount,
    uploadAvatar,
    removeAvatar,
    getAvatarInfo,
    logout
  }
})