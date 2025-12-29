import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import movieService from '@/services/movie'
import { useTaskPoller } from './useTaskPoller'

/**
 * 分镜工作流管理
 * 遵循架构：使用movieService而非直接调用api
 */
export function useShotWorkflow(script) {
    const extracting = ref(false)
    const generatingKeyframes = ref(new Set()) // 使用Set跟踪多个并发生成
    const extractingScenes = ref(new Set()) // 跟踪正在提取的场景
    const batchGenerating = ref(false) // 批量生成loading状态

    const allShots = computed(() => {
        if (!script.value?.scenes) return []
        return script.value.scenes.flatMap(scene =>
            scene.shots.map(shot => ({ ...shot, scene_id: scene.id }))
        ).sort((a, b) => a.order_index - b.order_index)
    })

    // 按场景分组的分镜数据
    const sceneGroups = computed(() => {
        if (!script.value?.scenes) return []
        return script.value.scenes.map(scene => ({
            scene,
            shots: scene.shots || []
        })).filter(group => group.shots.length > 0)
    })

    const extractShots = async (scriptId, apiKeyId, model, loadScript) => {
        extracting.value = true
        try {
            const response = await movieService.extractShots(scriptId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('分镜提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`分镜提取完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    extracting.value = false
                    // 只刷新script数据，不刷新整个页面
                    if (script.value?.chapter_id && loadScript) {
                        await loadScript(script.value.chapter_id, true) // skipStepUpdate=true
                    }
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extracting.value = false
                })
            }
        } catch (error) {
            ElMessage.error('分镜提取失败')
            extracting.value = false
        }
    }

    const generateKeyframes = async (scriptId, apiKeyId, model, loadScript) => {
        batchGenerating.value = true // 设置loading状态
        try {
            const response = await movieService.generateKeyframes(scriptId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('关键帧生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    batchGenerating.value = false // 清除loading状态
                    if (result.failed > 0) {
                        ElMessage.warning(`关键帧生成部分完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    } else {
                        ElMessage.success(`关键帧生成完成: 共 ${result.success} 个分镜`)
                    }
                    // 只刷新script数据，不刷新整个页面
                    if (script.value?.chapter_id && loadScript) {
                        await loadScript(script.value.chapter_id, true) // skipStepUpdate=true
                    }
                }, (error) => {
                    batchGenerating.value = false // 清除loading状态
                    ElMessage.error(`生成失败: ${error.message}`)
                })
            } else {
                batchGenerating.value = false
            }
        } catch (error) {
            batchGenerating.value = false // 清除loading状态
            ElMessage.error('关键帧生成失败')
        }
    }

    const generateSingleKeyframe = async (shotId, apiKeyId, model, prompt, loadScript) => {
        generatingKeyframes.value.add(shotId)
        try {
            const response = await movieService.generateSingleKeyframe(shotId, {
                api_key_id: apiKeyId,
                model,
                prompt
            })

            if (response.task_id) {
                ElMessage.success('关键帧生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id,
                    // Success callback
                    async () => {
                        ElMessage.success('关键帧生成完成')
                        generatingKeyframes.value.delete(shotId)
                        // 只刷新script数据，不刷新整个页面
                        if (script.value?.chapter_id && loadScript) {
                            await loadScript(script.value.chapter_id, true) // skipStepUpdate=true
                        }
                    },
                    // Error callback
                    (error) => {
                        ElMessage.error(`生成失败: ${error.message}`)
                        generatingKeyframes.value.delete(shotId)
                    }
                )
            } else {
                generatingKeyframes.value.delete(shotId)
            }
        } catch (error) {
            ElMessage.error('关键帧生成失败')
            generatingKeyframes.value.delete(shotId)
        }
    }

    const extractSingleSceneShots = async (sceneId, apiKeyId, model, loadScript) => {
        extractingScenes.value.add(sceneId)
        try {
            const response = await movieService.extractSingleSceneShots(sceneId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('单场景分镜提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`场景分镜提取完成: 生成 ${result.shot_count} 个分镜`)
                    extractingScenes.value.delete(sceneId)
                    // 只刷新script数据，不刷新整个页面
                    if (script.value?.chapter_id && loadScript) {
                        await loadScript(script.value.chapter_id, true) // skipStepUpdate=true
                    }
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extractingScenes.value.delete(sceneId)
                })
            }
        } catch (error) {
            ElMessage.error('单场景分镜提取失败')
            extractingScenes.value.delete(sceneId)
        }
    }

    return {
        allShots,
        sceneGroups,
        extracting,
        generatingKeyframes,
        extractingScenes,
        batchGenerating,
        extractShots,
        extractSingleSceneShots,
        generateKeyframes,
        generateSingleKeyframe
    }
}
