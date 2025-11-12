import { del, get, post, put, upload } from './api'

export const authService = {
  // 用户登录
  async login(credentials) {
    // 转换为表单数据格式
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    return await post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },

  // 用户注册
  async register(userData) {
    return await post('/auth/register', userData)
  },

  // 获取当前用户信息
  async getCurrentUser() {
    return await get('/users/me')
  },

  // 更新用户信息
  async updateProfile(userData) {
    return await put('/users/me', userData)
  },

  // 修改密码
  async changePassword(passwordData) {
    return await put('/users/me/password', passwordData)
  },

  // 获取用户统计信息
  async getUserStats() {
    return await get('/users/me/stats')
  },

  // 重新发送验证邮件
  async resendVerificationEmail() {
    return await post('/users/me/verify-email')
  },

  // 删除账户
  async deleteAccount(password) {
    return await put('/users/me/delete', { password })
  },

  // 上传头像
  async uploadAvatar(file, onProgress) {
    return await upload('/users/me/avatar', file, {
      onUploadProgress: onProgress
    })
  },

  // 删除头像
  async deleteAvatar() {
    return await del('/users/me/avatar')
  },

  // 获取头像信息
  async getAvatarInfo() {
    return await get('/users/me/avatar/info')
  }
}

export default authService