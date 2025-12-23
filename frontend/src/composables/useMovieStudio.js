import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import movieService from '@/services/movie'
import api from '@/services/api'
import { apiKeysService } from '@/services/apiKeys'
import chaptersService from '@/services/chapters'
import { useTaskPoller } from '@/composables/useTaskPoller'

export function useMovieStudio() {
    const route = useRoute()
    const router = useRouter()

    // 状态
    const selectedChapterId = ref(route.params.chapterId || null)
    const projectId = ref(null)
    const chapter = ref(null)
    const script = ref(null)
    const characters = ref([])
    const apiKeys = ref([])
    const loading = ref(false)
    const generatingScript = ref(false)
    const extractingCharacters = ref(false)
    const generatingKeyframes = ref(false)
    const batchProducing = ref(false)
    const generatingAvatarId = ref(null)
    const selectedCharacter = ref(null)
    const showCastManager = ref(true)
    const showGenerateDialog = ref(false)
    const dialogMode = ref('script')
    const modelOptions = ref([])
    const loadingModels = ref(false)
    const selectedShotId = ref(null)
    const showVideo = ref({})
    const autoRefreshTimer = ref(null)
    const checkingCompletion = ref(false)
    const completionStatus = ref(null)

    const genConfig = ref({
        api_key_id: '',
        model: '',
        style: 'cinematic',
        prompt: ''
    })

    const { startPolling, isPolling, taskStatus, taskStatistics, terminateTask, taskResult } = useTaskPoller()

    const STYLE_PROMPTS = {
        cinematic: "Cinematic lighting, movie still, 8k, photorealistic, dramatic, highly detailed face",
        anime: "Anime style, vibrant colors, detailed line art, digital illustration, clean lines",
        cyberpunk: "Cyberpunk style, neon lights, high tech low life, futuristic atmosphere, blue and pink lighting",
        oil_painting: "Oil painting style, brush strokes, classical art, rich colors, textured canvas"
    }

    // 计算属性
    const canPrepareMaterials = computed(() => completionStatus.value?.can_transition)
    const allCharactersReady = computed(() => {
        if (characters.value.length === 0) return true
        return characters.value.every(c => !!c.avatar_url)
    })

    // 方法
    const initProject = async () => {
        if (route.query.projectId) {
            projectId.value = route.query.projectId
            return
        }
        if (selectedChapterId.value) {
            try {
                const chap = await chaptersService.getChapter(selectedChapterId.value)
                projectId.value = chap.project_id
            } catch (e) {
                console.error("Failed to fetch project id from chapter", e)
            }
        }
    }

    const loadData = async (targetChapterId = selectedChapterId.value, isAutoRefresh = false) => {
        if (!targetChapterId) return

        if (!isAutoRefresh) loading.value = true
        try {
            chapter.value = await chaptersService.getChapter(targetChapterId)
            script.value = await movieService.getScript(targetChapterId).catch(() => null)

            if (chapter.value?.project_id) {
                projectId.value = chapter.value.project_id
                characters.value = await movieService.getCharacters(chapter.value.project_id)
            }

            if (!isAutoRefresh) {
                const keys = await apiKeysService.getAPIKeys()
                apiKeys.value = keys.api_keys || []
            }

            if (script.value) {
                checkCompletion()
                checkNeedsRefresh()
            }
        } catch (error) {
            console.error("Failed to load movie studio data", error)
        } finally {
            if (!isAutoRefresh) loading.value = false
        }
    }

    const checkNeedsRefresh = () => {
        const hasProcessing = script.value?.scenes.some(s =>
            s.shots.some(shot => shot.status === 'processing' || (!shot.first_frame_url && script.value))
        )

        if (hasProcessing) {
            if (!autoRefreshTimer.value) {
                autoRefreshTimer.value = setInterval(() => loadData(selectedChapterId.value, true), 15000)
            }
        } else {
            if (autoRefreshTimer.value) {
                clearInterval(autoRefreshTimer.value)
                autoRefreshTimer.value = null
            }
        }
    }

    const checkCompletion = async () => {
        if (!script.value) return
        try {
            checkingCompletion.value = true
            completionStatus.value = await movieService.checkScriptCompletion(script.value.id)
        } catch (e) {
            console.error("Failed to check completion", e)
        } finally {
            checkingCompletion.value = false
        }
    }

    const fetchModels = async () => {
        const newKeyId = genConfig.value.api_key_id
        if (!newKeyId) {
            modelOptions.value = []
            return
        }

        try {
            loadingModels.value = true
            const isText = ['script', 'character'].includes(dialogMode.value)
            const type = isText ? 'text' : 'image'

            const models = await api.get(`/api-keys/${newKeyId}/models?type=${type}`)
            modelOptions.value = models || []

            const key = apiKeys.value.find(k => k.id === newKeyId)
            if (key && ['google', 'custom', 'siliconflow'].includes(key.provider.toLowerCase())) {
                const defaultModel = isText ? 'gemini-3-flash-preview' : 'gemini-3-pro-image-preview'
                if (!modelOptions.value.includes(defaultModel)) {
                    modelOptions.value.unshift(defaultModel)
                }
            }

            if (modelOptions.value.length > 0 && !modelOptions.value.includes(genConfig.value.model)) {
                genConfig.value.model = modelOptions.value[0]
            }
        } catch (err) {
            console.error(err)
            ElMessage.error('获取模型列表失败')
        } finally {
            loadingModels.value = false
        }
    }

    const handleGenerateScript = () => {
        if (!selectedChapterId.value) return
        dialogMode.value = 'script'
        showGenerateDialog.value = true
    }

    const confirmGenerate = async () => {
        if (!genConfig.value.api_key_id) {
            ElMessage.warning('请选择 API Key')
            return
        }
        showGenerateDialog.value = false
        generatingScript.value = true
        try {
            const response = await movieService.generateScript(selectedChapterId.value, genConfig.value)
            if (response?.task_id) {
                ElMessage.success('剧本生成任务已提交，正在后台处理...')
                startPolling(response.task_id, async () => {
                    ElMessage.success('剧本生成完成！')
                    await loadData(selectedChapterId.value)
                    generatingScript.value = false
                }, (error) => {
                    ElMessage.error(`剧本生成失败: ${error.message || '未知错误'}`)
                    generatingScript.value = false
                })
            } else {
                await loadData(selectedChapterId.value)
                generatingScript.value = false
            }
        } catch (err) {
            ElMessage.error('任务提交失败')
            generatingScript.value = false
        }
    }

    const handleDetectCharacters = () => {
        if (!script.value) return
        dialogMode.value = 'character'
        showGenerateDialog.value = true
        if (genConfig.value.api_key_id) fetchModels()
    }

    const confirmExtractCharacters = async () => {
        if (!genConfig.value.api_key_id) {
            ElMessage.warning('请选择 API Key')
            return
        }
        if (!script.value?.id) return

        showGenerateDialog.value = false
        extractingCharacters.value = true
        try {
            const response = await movieService.extractCharacters(script.value.id, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })

            if (response?.task_id) {
                ElMessage.success('角色提取任务已提交...')
                startPolling(response.task_id, async () => {
                    ElMessage.success('角色提取完成')
                    if (chapter.value?.project_id) {
                        characters.value = await movieService.getCharacters(chapter.value.project_id)
                    }
                    extractingCharacters.value = false
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extractingCharacters.value = false
                })
            } else {
                // Initial implementation might have been sync if no task_id, but backend uses Celery
                // Keep compatibility if it returns chars directly (unlikely based on backend code)
                if (chapter.value?.project_id) {
                    characters.value = await movieService.getCharacters(chapter.value.project_id)
                }
                extractingCharacters.value = false
            }
        } catch (e) {
            ElMessage.error('角色提取失败')
            extractingCharacters.value = false
        }
    }

    const handleGenerateAvatar = (char) => {
        selectedCharacter.value = char
        dialogMode.value = 'avatar'
        // 优先使用generated_prompt(三视图提示词),如果不存在则使用旧逻辑
        if (char.generated_prompt) {
            genConfig.value.prompt = char.generated_prompt
        } else {
            const stylePrompt = STYLE_PROMPTS[genConfig.value.style] || STYLE_PROMPTS.cinematic
            genConfig.value.prompt = `${stylePrompt}, ${char.visual_traits}`
        }
        showGenerateDialog.value = true
    }

    const confirmAvatar = async () => {
        if (!genConfig.value.api_key_id) {
            ElMessage.warning('请选择 API Key')
            return
        }
        const char = selectedCharacter.value
        showGenerateDialog.value = false
        generatingAvatarId.value = char.id
        try {
            const response = await movieService.generateCharacterAvatar(char.id, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model,
                style: genConfig.value.style,
                prompt: genConfig.value.prompt
            })
            if (response?.task_id) {
                ElMessage.success('人物绘图任务已提交...')
                startPolling(response.task_id, async () => {
                    ElMessage.success('人物形象生成成功')
                    if (chapter.value?.project_id) {
                        characters.value = await movieService.getCharacters(chapter.value.project_id)
                    }
                    generatingAvatarId.value = null
                }, (error) => {
                    ElMessage.error(`生成失败: ${error.message}`)
                    generatingAvatarId.value = null
                })
            }
        } catch (err) {
            ElMessage.error('无法启动形象生成')
            generatingAvatarId.value = null
        }
    }

    const handleDeleteCharacter = async (char) => {
        try {
            await ElMessageBox.confirm(
                `确定要删除角色 "${char.name}" 吗?此操作不可恢复。`,
                '删除角色',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )

            await movieService.deleteCharacter(char.id)
            ElMessage.success('角色已删除')

            // 刷新角色列表
            if (chapter.value?.project_id) {
                characters.value = await movieService.getCharacters(chapter.value.project_id)
            }
        } catch (err) {
            if (err !== 'cancel') {
                ElMessage.error('删除失败')
            }
        }
    }

    const handleBatchGenerateAvatars = async () => {
        // 显示弹窗让用户选择API Key和模型
        dialogMode.value = 'batch-avatars'
        showGenerateDialog.value = true
    }

    const confirmBatchGenerateAvatars = async () => {
        if (!genConfig.value.api_key_id) {
            ElMessage.warning('请选择 API Key')
            return
        }

        showGenerateDialog.value = false
        try {
            const response = await movieService.batchGenerateAvatars(projectId.value, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })

            if (response?.task_id) {
                ElMessage.success('批量生成任务已提交...')
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`批量生成完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    if (chapter.value?.project_id) {
                        characters.value = await movieService.getCharacters(chapter.value.project_id)
                    }
                }, (error) => {
                    ElMessage.error(`批量生成失败: ${error.message}`)
                })
            }
        } catch (err) {
            ElMessage.error('无法启动批量生成')
        }
    }

    const handleGenerateKeyframes = () => {
        if (!script.value) return
        dialogMode.value = 'keyframes'
        showGenerateDialog.value = true
    }

    const confirmKeyframes = async () => {
        if (!genConfig.value.api_key_id) {
            ElMessage.warning('请选择 API Key')
            return
        }
        showGenerateDialog.value = false
        generatingKeyframes.value = true
        try {
            const response = await movieService.generateKeyframes(script.value.id, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })
            if (response?.task_id) {
                ElMessage.success('批量生成首尾帧任务已提交...')
                startPolling(response.task_id, async (result) => {
                    if (result.failed > 0) {
                        ElMessage.warning(`绘图部分完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    } else {
                        ElMessage.success(`批量绘图已全部完成: 共 ${result.success} 个分镜`)
                    }
                    loadData(selectedChapterId.value)
                    generatingKeyframes.value = false
                }, (error) => {
                    ElMessage.error(`任务失败: ${error.message}`)
                    generatingKeyframes.value = false
                })
            }
        } catch (err) {
            ElMessage.error('无法启动批量绘图')
            generatingKeyframes.value = false
        }
    }

    const handleProduceShot = async (shot) => {
        selectedShotId.value = shot.id
        if (!genConfig.value.api_key_id) {
            dialogMode.value = 'produce-single'
            showGenerateDialog.value = true
            return
        }
        confirmProduceSingle()
    }

    const confirmProduceSingle = async () => {
        if (!genConfig.value.api_key_id) return
        const shotId = selectedShotId.value
        showGenerateDialog.value = false
        try {
            await movieService.produceShot(shotId, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })
            ElMessage.success('视频生产任务已提交')
            loadData(selectedChapterId.value)
        } catch (err) { ElMessage.error('视频生产失败') }
    }

    const handleBatchProduceVideos = async () => {
        if (!genConfig.value.api_key_id) {
            dialogMode.value = 'produce-batch'
            showGenerateDialog.value = true
            return
        }
        confirmProduceBatch()
    }

    const confirmProduceBatch = async () => {
        if (!genConfig.value.api_key_id) return
        showGenerateDialog.value = false
        batchProducing.value = true
        try {
            const response = await movieService.batchProduceVideos(script.value.id, {
                api_key_id: genConfig.value.api_key_id,
                model: 'veo3.1-fast'
            })
            if (response?.task_id) {
                ElMessage.success('批量视频生产任务已启动, 正在排队...')
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`批量生产完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    loadData(selectedChapterId.value)
                    batchProducing.value = false
                }, (error) => {
                    ElMessage.error(`任务失败: ${error.message}`)
                    batchProducing.value = false
                })
            } else {
                ElMessage.success(response.message || '批量视频生产任务已启动')
                await loadData(selectedChapterId.value)
                batchProducing.value = false
            }
        } catch (err) {
            ElMessage.error('启动批量生产失败')
            batchProducing.value = false
        }
    }

    const handlePrepareMaterials = async () => {
        if (!selectedChapterId.value) return
        try {
            await movieService.prepareChapterMaterials(selectedChapterId.value)
            ElMessage.success("章节状态更新成功！已进入素材准备阶段")
            loadData()
        } catch (e) { ElMessage.error(e.response?.data?.detail || "更新状态失败") }
    }

    const handleRegenerateKeyframe = async () => {
        const shotId = selectedShotId.value
        showGenerateDialog.value = false
        try {
            await movieService.regenerateKeyframe(shotId, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })
            ElMessage.success('首帧重制任务已提交')
            loadData(selectedChapterId.value)
        } catch (err) { ElMessage.error('失败') }
    }

    const handleRegenerateLastFrame = async () => {
        const shotId = selectedShotId.value
        showGenerateDialog.value = false
        try {
            await movieService.regenerateLastFrame(shotId, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })
            ElMessage.success('尾帧重制任务已提交')
            loadData(selectedChapterId.value)
        } catch (err) { ElMessage.error('失败') }
    }

    const handleRegenerateVideo = async () => {
        const shotId = selectedShotId.value
        showGenerateDialog.value = false
        try {
            await movieService.regenerateVideo(shotId, {
                api_key_id: genConfig.value.api_key_id,
                model: genConfig.value.model
            })
            ElMessage.success('视频重制任务已提交')
            loadData(selectedChapterId.value)
        } catch (err) { ElMessage.error('失败') }
    }

    const toggleShotView = (shotId, visible) => {
        showVideo.value[shotId] = visible
    }

    const goBack = () => {
        if (projectId.value) router.push({ name: 'ProjectDetail', params: { projectId: projectId.value } })
        else router.push('/projects')
    }

    const handleUpdateShotPrompt = async (shotId, type, content) => {
        try {
            const data = {}
            if (type === 'first') data.first_frame_prompt = content
            else if (type === 'last') data.last_frame_prompt = content
            else return

            await movieService.updateShot(shotId, data)
            ElMessage.success('提示词更新成功')
        } catch (error) {
            console.error('Update shot prompt failed:', error)
            ElMessage.error('更新失败')
        }
    }

    const handleShotCommand = (command, shot) => {
        selectedShotId.value = shot.id
        if (['regen-keyframe', 'regen-last-frame', 'regen-video'].includes(command)) {
            dialogMode.value = command
            showGenerateDialog.value = true
        } else if (command === 'switch-video') {
            showVideo.value[shot.id] = true
        }
    }

    // 生命周期与 Watchers
    watch(showGenerateDialog, (val) => {
        if (val && genConfig.value.api_key_id) {
            fetchModels()
        }
    })

    watch(selectedChapterId, (newId) => {
        if (newId) {
            if (route.params.chapterId !== newId) {
                router.push({ name: 'MovieStudio', params: { chapterId: newId } })
            }
            loadData(newId)
        }
    })

    watch(() => genConfig.value.style, (newStyle) => {
        if (dialogMode.value === 'avatar' && selectedCharacter.value) {
            // 如果有generated_prompt,则不随style变化而改变(三视图提示词已包含完整信息)
            if (!selectedCharacter.value.generated_prompt) {
                const stylePrompt = STYLE_PROMPTS[newStyle] || STYLE_PROMPTS.cinematic
                genConfig.value.prompt = `${stylePrompt}, ${selectedCharacter.value.visual_traits}`
            }
        }
    })

    onMounted(async () => {
        await initProject()
        if (selectedChapterId.value) loadData(selectedChapterId.value)
    })

    onUnmounted(() => {
        if (autoRefreshTimer.value) clearInterval(autoRefreshTimer.value)
    })

    return {
        // 状态
        selectedChapterId, projectId, chapter, script, characters, apiKeys,
        loading, generatingScript, extractingCharacters, generatingKeyframes,
        batchProducing, generatingAvatarId, selectedCharacter, showCastManager,
        showGenerateDialog, dialogMode, modelOptions, loadingModels,
        selectedShotId, showVideo, completionStatus, checkingCompletion,
        genConfig, isPolling, taskStatus, taskStatistics, taskResult,
        terminateTask,

        // 计算属性
        canPrepareMaterials, allCharactersReady,

        // 方法
        loadData, fetchModels, handleGenerateScript, confirmGenerate,
        handleDetectCharacters, confirmExtractCharacters, handleGenerateAvatar, confirmAvatar,
        handleDeleteCharacter, handleBatchGenerateAvatars, confirmBatchGenerateAvatars,
        handleGenerateKeyframes, confirmKeyframes, handleProduceShot,
        confirmProduceSingle, handleBatchProduceVideos, confirmProduceBatch,
        handlePrepareMaterials, handleRegenerateKeyframe, handleRegenerateLastFrame,
        handleRegenerateVideo, toggleShotView, goBack, handleShotCommand,
        checkCompletion, handleUpdateShotPrompt, terminateTask
    }
}
