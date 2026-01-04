import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCharacterWorkflow } from './useCharacterWorkflow'
import { useSceneWorkflow } from './useSceneWorkflow'
import { useShotWorkflow } from './useShotWorkflow'
import { useTransitionWorkflow } from './useTransitionWorkflow'
import apiKeysService from '@/services/apiKeys'

/**
 * 电影工作流主控制器
 * 完全参照 useDirectorEngine 的实现方式
 */
export function useMovieWorkflow() {
    const route = useRoute()
    const router = useRouter()

    const selectedChapterId = ref(route.params.chapterId || null)
    const projectId = ref(route.params.projectId || null)
    const currentStep = ref(0)
    const loading = ref(false)
    const apiKeys = ref([])

    console.log('useMovieWorkflow init:', {
        chapterId: selectedChapterId.value,
        projectId: projectId.value,
        routeParams: route.params
    })

    // Initialize workflows
    const characterWorkflow = useCharacterWorkflow(projectId)
    const sceneWorkflow = useSceneWorkflow()
    const shotWorkflow = useShotWorkflow(sceneWorkflow.script)
    const transitionWorkflow = useTransitionWorkflow()

    // 加载API Keys - 完全照搬 useDirectorEngine 的实现
    const loadApiKeys = async () => {
        const res = await apiKeysService.getAPIKeys()
        apiKeys.value = res.api_keys || []
        console.log('Loaded API keys:', apiKeys.value)
    }

    // Computed states
    const canExtractScenes = computed(() => {
        return characterWorkflow.characters.value.length > 0
    })

    const canExtractShots = computed(() => {
        return sceneWorkflow.script.value?.scenes?.length > 0
    })

    const canGenerateSceneImages = computed(() => {
        return shotWorkflow.allShots.value.length > 0
    })

    const canGenerateKeyframes = computed(() => {
        // 场景图不再是必需的，有角色头像和分镜即可生成关键帧
        return shotWorkflow.allShots.value.length > 0 &&
            characterWorkflow.characters.value.every(c => c.avatar_url)
    })

    const canCreateTransitions = computed(() => {
        return shotWorkflow.allShots.value.every(s => s.keyframe_url)
    })

    const canGenerateTransitionVideos = computed(() => {
        return transitionWorkflow.transitions.value.length > 0
    })

    // Auto-determine current step based on data
    const determineCurrentStep = () => {
        if (!sceneWorkflow.script.value) {
            currentStep.value = 0 // Characters
        } else if (!sceneWorkflow.script.value.scenes?.length) {
            currentStep.value = 1 // Scenes
        } else if (!shotWorkflow.allShots.value.length) {
            currentStep.value = 2 // Shots
        } else if (!shotWorkflow.allShots.value.every(s => s.keyframe_url)) {
            // 跳过场景图检查，直接到关键帧
            currentStep.value = 4 // Keyframes
        } else if (!transitionWorkflow.transitions.value.length) {
            currentStep.value = 5 // Transitions
        } else {
            currentStep.value = 6 // Final
        }
    }

    // Load initial data
    const loadData = async (skipStepUpdate = false) => {
        if (!projectId.value) {
            console.warn('Cannot load data: missing projectId')
            return
        }

        loading.value = true
        try {
            // Always load characters first
            await characterWorkflow.loadCharacters()

            // Try to load script if chapter is selected
            if (selectedChapterId.value) {
                try {
                    await sceneWorkflow.loadScript(selectedChapterId.value)
                    if (sceneWorkflow.script.value) {
                        await transitionWorkflow.loadTransitions(sceneWorkflow.script.value.id)
                    }
                } catch (error) {
                    console.log('No script found for this chapter yet')
                }
            }

            // 只在非手动刷新时自动确定步骤
            if (!skipStepUpdate) {
                determineCurrentStep()
            }
        } catch (error) {
            console.error('Failed to load data:', error)
        } finally {
            loading.value = false
        }
    }

    const goBack = () => {
        if (projectId.value) {
            router.push({ name: 'ProjectDetail', params: { projectId: projectId.value } })
        } else {
            router.push('/projects')
        }
    }

    // Watch for chapter changes and update URL
    watch(selectedChapterId, (newId, oldId) => {
        if (newId && newId !== oldId && projectId.value) {
            // Update URL to reflect current chapter selection
            router.replace({
                name: 'MovieStudio',
                params: {
                    projectId: projectId.value,
                    chapterId: newId
                }
            })
            loadData()
        }
    })

    // Watch for route changes
    watch(() => route.params, (newParams) => {
        console.log('Route params changed:', newParams)
        if (newParams.projectId) {
            projectId.value = newParams.projectId
        }
        if (newParams.chapterId) {
            selectedChapterId.value = newParams.chapterId
        }
    }, { deep: true })

    // onMounted - 完全照搬 useDirectorEngine 的顺序
    onMounted(async () => {
        // 先加载 API keys
        await loadApiKeys()

        // 再加载数据
        if (projectId.value) {
            await loadData()
        }
    })

    return {
        // State
        selectedChapterId,
        projectId,
        currentStep,
        loading,
        apiKeys,

        // Workflows
        characterWorkflow,
        sceneWorkflow,
        shotWorkflow,
        transitionWorkflow,

        // Computed
        canExtractScenes,
        canExtractShots,
        canGenerateSceneImages,
        canGenerateKeyframes,
        canCreateTransitions,
        canGenerateTransitionVideos,

        // Methods
        loadData,
        goBack
    }
}
