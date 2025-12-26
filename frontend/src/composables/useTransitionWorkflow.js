import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import movieService from '@/services/movie'
import { useTaskPoller } from './useTaskPoller'

/**
 * 过渡视频工作流管理
 * 遵循架构：使用movieService而非直接调用api
 */
export function useTransitionWorkflow() {
    const transitions = ref([])
    const creating = ref(false)
    const generating = ref(false)
    const generatingIds = ref(new Set()) // 跟踪单个生成状态

    const loadTransitions = async (scriptId) => {
        if (!scriptId) return
        try {
            const response = await movieService.getTransitions(scriptId)
            transitions.value = response.transitions || []
        } catch (error) {
            console.error('Failed to load transitions:', error)
            transitions.value = []
        }
    }

    const createTransitions = async (scriptId, apiKeyId, model) => {
        creating.value = true
        try {
            const response = await movieService.createTransitions(scriptId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`过渡创建完成: ${result.success} 个过渡`)
                    await loadTransitions(scriptId)
                    creating.value = false
                }, (error) => {
                    ElMessage.error(`创建失败: ${error.message}`)
                    creating.value = false
                })
            }
        } catch (error) {
            ElMessage.error('过渡创建失败')
            creating.value = false
        }
    }

    const generateTransitionVideos = async (scriptId, apiKeyId, videoModel) => {
        generating.value = true
        try {
            const response = await movieService.generateTransitionVideos(scriptId, {
                api_key_id: apiKeyId,
                video_model: videoModel
            })

            if (response.task_id) {
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`视频生成完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    await loadTransitions(scriptId)
                    generating.value = false
                }, (error) => {
                    ElMessage.error(`生成失败: ${error.message}`)
                    generating.value = false
                })
            }
        } catch (error) {
            ElMessage.error('视频生成失败')
            generating.value = false
        }
    }

    const updateTransitionPrompt = async (transitionId, prompt) => {
        try {
            await movieService.updateTransitionPrompt(transitionId, prompt)
            ElMessage.success('提示词更新成功')
            return true
        } catch (error) {
            ElMessage.error('提示词更新失败')
            return false
        }
    }

    // 生成单个过渡视频
    const generateSingleVideo = async (transitionId, scriptId, apiKeyId, videoModel, prompt) => {
        generatingIds.value.add(transitionId)
        try {
            const response = await movieService.generateSingleTransition(transitionId, {
                api_key_id: apiKeyId,
                video_model: videoModel,
                prompt: prompt
            })

            if (response.task_id) {
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success('视频生成完成')
                    await loadTransitions(scriptId)
                    generatingIds.value.delete(transitionId)
                }, (error) => {
                    ElMessage.error(`生成失败: ${error.message}`)
                    generatingIds.value.delete(transitionId)
                })
            }
            return response
        } catch (error) {
            ElMessage.error('视频生成失败')
            generatingIds.value.delete(transitionId)
            throw error
        }
    }

    const deleteTransition = async (transitionId, scriptId) => {
        try {
            await movieService.deleteTransition(transitionId)
            ElMessage.success('删除成功')
            await loadTransitions(scriptId)
            return true
        } catch (error) {
            ElMessage.error('删除失败')
            return false
        }
    }

    return {
        transitions,
        creating,
        generating,
        generatingIds,
        loadTransitions,
        createTransitions,
        generateTransitionVideos,
        updateTransitionPrompt,
        generateSingleVideo,
        deleteTransition
    }
}
