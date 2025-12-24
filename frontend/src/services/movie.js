import api, { get, post, put, del } from './api'

/**
 * 电影生成相关服务
 * 遵循项目架构：所有API调用通过service层，composables不直接使用api
 */
export const movieService = {
    // ==================== 角色管理 ====================

    /**
     * 获取项目的角色列表
     */
    getCharacters(projectId) {
        return get(`/movie/projects/${projectId}/characters`)
    },

    /**
     * 从剧本中提取角色
     */
    extractCharacters(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/extract-characters`, data)
    },

    /**
     * 生成角色形象
     */
    generateCharacterAvatar(characterId, data) {
        return post(`/movie/characters/${characterId}/generate`, data)
    },

    /**
     * 批量生成角色定妆照
     */
    batchGenerateAvatars(projectId, data) {
        return post(`/movie/projects/${projectId}/characters/batch-generate`, data)
    },

    /**
     * 删除角色
     */
    deleteCharacter(characterId) {
        return api.delete(`/movie/characters/${characterId}`)
    },

    // ==================== 场景管理 ====================

    /**
     * 获取章节关联的剧本详情
     */
    getScript(chapterId) {
        return get(`/movie/chapters/${chapterId}/script`)
    },

    /**
     * 从章节提取场景（新架构）
     */
    extractScenes(chapterId, data) {
        return post(`/movie/chapters/${chapterId}/scenes`, data)
    },

    // ==================== 分镜管理 ====================

    /**
     * 从剧本提取分镜
     */
    extractShots(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/extract-shots`, data)
    },

    /**
     * 更新分镜信息
     */
    updateShot(shotId, data) {
        return put(`/movie/shots/${shotId}`, data)
    },

    // ==================== 关键帧管理 ====================

    /**
     * 为单个分镜生成关键帧
     */
    generateSingleKeyframe(shotId, data) {
        return post(`/movie/shots/${shotId}/generate-keyframe`, data)
    },

    /**
     * 为剧本批量生成分镜关键帧
     */
    generateKeyframes(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/generate-keyframes`, data)
    },

    // ==================== 过渡视频管理 ====================

    /**
     * 创建过渡视频记录
     */
    createTransitions(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/create-transitions`, data)
    },

    /**
     * 批量生成过渡视频
     */
    generateTransitionVideos(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/generate-transition-videos`, data)
    },

    /**
     * 生成单个过渡视频
     */
    generateSingleTransition(transitionId, data) {
        return post(`/movie/transitions/${transitionId}/generate-video`, data)
    },

    /**
     * 获取剧本的过渡列表
     */
    getTransitions(scriptId) {
        return get(`/movie/scripts/${scriptId}/transitions`)
    },

    /**
     * 获取单个过渡
     */
    getTransition(transitionId) {
        return get(`/movie/transitions/${transitionId}`)
    },

    /**
     * 更新过渡提示词
     */
    updateTransitionPrompt(transitionId, prompt) {
        return put(`/movie/transitions/${transitionId}`, { video_prompt: prompt })
    },

    /**
     * 删除过渡
     */
    deleteTransition(transitionId) {
        return del(`/movie/transitions/${transitionId}`)
    }
}

export default movieService
