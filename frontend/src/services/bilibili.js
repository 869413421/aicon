/**
 * Bilibili发布服务
 */

import { get, post } from './api'

export const bilibiliService = {
    /**
     * 二维码登录
     */
    async loginByQrcode() {
        return await post('/bilibili/login/qrcode')
    },

    /**
     * 发布视频到B站
     */
    async publishVideo(publishData) {
        return await post('/bilibili/publish', publishData)
    },

    /**
     * 获取发布任务状态
     */
    async getTaskStatus(taskId) {
        return await get(`/bilibili/tasks/${taskId}`)
    },

    /**
     * 获取发布任务列表
     */
    async getTasks(params = {}) {
        return await get('/bilibili/tasks', { params })
    },

    /**
     * 获取B站分区选项
     */
    async getTidOptions() {
        return await get('/bilibili/tid-options')
    }
}

export default bilibiliService
