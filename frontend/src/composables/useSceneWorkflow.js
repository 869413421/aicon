import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import movieService from '@/services/movie'
import { useTaskPoller } from './useTaskPoller'

/**
 * 场景工作流管理
 * 遵循架构：使用movieService而非直接调用api
 */
export function useSceneWorkflow() {
    const script = ref(null)
    const extracting = ref(false)
    const generatingSceneImages = ref(new Set())

    const loadScript = async (chapterId) => {
        if (!chapterId) return
        try {
            const response = await movieService.getScript(chapterId)
            // response已经是data
            script.value = response
        } catch (error) {
            console.error('Failed to load script:', error)
            script.value = null
        }
    }

    const extractScenes = async (chapterId, apiKeyId, model) => {
        extracting.value = true
        try {
            const response = await movieService.extractScenes(chapterId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('场景提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async () => {
                    ElMessage.success('场景提取完成')
                    await loadScript(chapterId)
                    extracting.value = false
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extracting.value = false
                })
            }
        } catch (error) {
            ElMessage.error('场景提取失败')
            extracting.value = false
        }
    }

    const generateSceneImages = async (scriptId, apiKeyId, model) => {
        try {
            const response = await movieService.batchGenerateSceneImages(scriptId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('场景图批量生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async () => {
                    ElMessage.success('场景图批量生成完成')
                    // 重新加载script以获取更新的场景图
                    if (script.value?.chapter_id) {
                        await loadScript(script.value.chapter_id)
                    }
                }, (error) => {
                    ElMessage.error(`场景图生成失败: ${error.message}`)
                })
            }
        } catch (error) {
            ElMessage.error('场景图生成失败')
        }
    }

    const generateSingleSceneImage = async (sceneId, apiKeyId, model, prompt) => {
        generatingSceneImages.value.add(sceneId)
        try {
            const response = await movieService.generateSceneImage(sceneId, {
                api_key_id: apiKeyId,
                model,
                prompt
            })

            if (response.task_id) {
                ElMessage.success('场景图生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async () => {
                    ElMessage.success('场景图生成完成')
                    generatingSceneImages.value.delete(sceneId)
                    // 重新加载script
                    if (script.value?.chapter_id) {
                        await loadScript(script.value.chapter_id)
                    }
                }, (error) => {
                    ElMessage.error(`场景图生成失败: ${error.message}`)
                    generatingSceneImages.value.delete(sceneId)
                })
            }
        } catch (error) {
            ElMessage.error('场景图生成失败')
            generatingSceneImages.value.delete(sceneId)
        }
    }

    return {
        script,
        extracting,
        generatingSceneImages,
        loadScript,
        extractScenes,
        generateSceneImages,
        generateSingleSceneImage
    }
}
