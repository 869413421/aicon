import { post, put, get, del, upload } from './api'

export const authService = {
  // 用户登录
  async login(credentials) {
    // 转换为表单数据格式
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response
  },

  // 用户注册
  async register(userData) {
    const response = await post('/auth/register', userData)
    return response
  },

  // 获取当前用户信息
  async getCurrentUser() {
    const response = await get('/users/me')
    return response
  },

  // 更新用户信息
  async updateProfile(userData) {
    const response = await put('/users/me', userData)
    return response
  },

  // 修改密码
  async changePassword(passwordData) {
    const response = await put('/users/me/password', passwordData)
    return response
  },

  // 获取用户统计信息
  async getUserStats() {
    const response = await get('/users/me/stats')
    return response
  },

  // 重新发送验证邮件
  async resendVerificationEmail() {
    const response = await post('/users/me/verify-email')
    return response
  },

  // 删除账户
  async deleteAccount(password) {
    const response = await put('/users/me/delete', { password })
    return response
  },

  // 上传头像
  async uploadAvatar(file, onProgress) {
    const response = await upload('/users/me/avatar', file, {
      onUploadProgress: onProgress
    })
    return response
  },

  // 删除头像
  async deleteAvatar() {
    const response = await del('/users/me/avatar')
    return response
  },

  // 获取头像信息
  async getAvatarInfo() {
    const response = await get('/users/me/avatar/info')
    return response
  }
}

export default authService