/**
 * 导出服务 - 处理章节导出相关功能
 */

import { post, get } from './api'

export const exportService = {
    /**
     * 导出章节为剪映格式
     * @param {string} chapterId - 章节ID
     * @returns {Promise} 导出结果
     */
    async exportToJianYing(chapterId) {
        return await post(`/export/jianying/${chapterId}`)
    },

    /**
     * 下载导出的文件
     * @param {string} downloadUrl - 下载URL
     * @param {string} filename - 文件名
     */
    async downloadFile(downloadUrl, filename) {
        try {
            // 从 localStorage 获取 token
            const token = localStorage.getItem('token')

            // 使用 fetch 下载文件,携带认证头
            const response = await fetch(downloadUrl, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (!response.ok) {
                throw new Error(`下载失败: ${response.statusText}`)
            }

            // 获取文件内容
            const blob = await response.blob()

            // 创建下载链接
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = filename
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()

            // 清理
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
        } catch (error) {
            console.error('文件下载失败:', error)
            throw error
        }
    }
}

export default exportService
