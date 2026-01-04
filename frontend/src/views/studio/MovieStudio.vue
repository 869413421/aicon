<template>
  <div class="movie-studio-layout">
    <!-- 侧边栏：章节选择 -->
    <div class="studio-sidebar-left">
      <ChapterSelector 
        v-model="selectedChapterId" 
        :project-id="projectId"
        ref="chapterSelectorRef"
        @create="handleChapterCreate"
      />
    </div>

    <!-- 主体内容区 -->
    <div class="studio-main">
      <!-- 顶部导航 -->
      <div class="studio-header">
        <el-button icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>电影工作室</h2>
        <div class="debug-info" v-if="!projectId">
          <el-alert type="error" :closable="false">
            缺少projectId参数，请从项目详情页进入
          </el-alert>
        </div>
      </div>

      <!-- 工作流步骤指示器 -->
      <WorkflowStepper :current-step="currentStep" @change-step="handleStepChange" />

      <!-- 内容区 -->
      <div class="studio-body" v-loading="loading">
        <div v-if="!selectedChapterId" class="empty-selection">
          <el-empty description="请从左侧选择一个章节开始制作" />
        </div>

        <div v-else class="workflow-content">
          <!-- 步骤0: 角色管理 -->
          <CharacterPanel
            v-show="currentStep === 0"
            :characters="characterWorkflow.characters.value"
            :extracting="characterWorkflow.extracting.value"
            :generating-ids="characterWorkflow.generatingIds.value"
            :batch-generating="characterWorkflow.batchGenerating.value"
            :can-extract="canExtractCharacters"
            :api-keys="apiKeys"
            @extract-characters="handleExtractCharacters"
            @generate-avatar="handleGenerateAvatar"
            @delete-character="handleDeleteCharacter"
            @batch-generate="handleBatchGenerateAvatars"
            @refresh="handleRefreshCharacters"
          />

          <!-- 步骤1: 场景提取 -->
          <ScenePanel
            v-show="currentStep === 1"
            :scenes="sceneWorkflow.script.value?.scenes || []"
            :extracting="sceneWorkflow.extracting.value"
            :can-extract="canExtractScenes"
            :api-keys="apiKeys"
            @extract-scenes="handleExtractScenes"
          />

          <!-- 步骤2: 分镜提取 -->
          <ShotPanel
            v-show="currentStep === 2"
            :scene-groups="shotWorkflow.sceneGroups.value"
            :extracting="shotWorkflow.extracting.value"
            :extracting-scenes="shotWorkflow.extractingScenes.value"
            :can-extract="canExtractShots"
            :api-keys="apiKeys"
            @extract-shots="handleExtractShots"
            @extract-single-scene-shots="handleExtractSingleSceneShots"
          />

          <!-- 步骤3: 场景图生成 -->
          <SceneImagePanel
            v-show="currentStep === 3"
            :scenes="sceneWorkflow.script.value?.scenes || []"
            :can-generate="canGenerateSceneImages"
            :api-keys="apiKeys"
            :generating-ids="sceneWorkflow.generatingSceneImages.value"
            :batch-generating="sceneWorkflow.batchGenerating.value"
            @batch-generate="handleBatchGenerateSceneImages"
            @generate-scene-image="handleGenerateSceneImage"
            @refresh="handleRefreshScenes"
          />

          <!-- 步骤4: 关键帧生成 -->
          <KeyframePanel
            v-show="currentStep === 4"
            :scene-groups="shotWorkflow.sceneGroups.value"
            :can-generate="canGenerateKeyframes"
            :api-keys="apiKeys"
            :generating-ids="shotWorkflow.generatingKeyframes.value"
            :batch-generating="shotWorkflow.batchGenerating.value"
            @batch-generate="handleBatchGenerateKeyframes"
            @generate-keyframe="handleGenerateSingleKeyframe"
            @refresh="handleRefreshKeyframes"
          />

          <!-- 步骤5: 过渡视频 -->
          <TransitionPanel
            v-show="currentStep === 5"
            :script-id="sceneWorkflow.script.value?.id"
            :transitions="transitionWorkflow.transitions.value"
            :creating="transitionWorkflow.creating.value"
            :generating="transitionWorkflow.generating.value"
            :can-create="canCreateTransitions"
            :can-generate="canGenerateTransitionVideos"
            :api-keys="apiKeys"
            @create-transitions="handleCreateTransitions"
            @generate-videos="handleGenerateTransitionVideos"
          />

          <!-- 步骤6: 最终合成 -->
          <div v-show="currentStep === 6" class="final-step">
            <el-result
              icon="success"
              title="所有步骤已完成"
              sub-title="检查素材准备情况，开始最终合成"
            >
              <template #extra>
                <el-space direction="vertical" :size="20" style="width: 100%;">
                  <el-button 
                    type="primary" 
                    size="large"
                    @click="handleCheckMaterials"
                    :loading="checkingMaterials"
                  >
                    检查素材并开始合成
                  </el-button>
                  
                  <!-- 素材检查结果 -->
                  <el-card v-if="materialCheckResult" class="material-check-card">
                    <template #header>
                      <div class="card-header">
                        <span>素材检查结果</span>
                        <el-tag 
                          :type="materialCheckResult.ready ? 'success' : 'warning'"
                          size="large"
                        >
                          {{ materialCheckResult.ready ? '✓ 全部就绪' : '⚠ 有缺失' }}
                        </el-tag>
                      </div>
                    </template>
                    
                    <el-descriptions :column="1" border>
                      <el-descriptions-item label="角色头像">
                        <el-tag :type="materialCheckResult.characters.ready ? 'success' : 'danger'">
                          {{ materialCheckResult.characters.ready ? '✓' : '✗' }}
                          {{ materialCheckResult.characters.total }} 个角色
                          <template v-if="!materialCheckResult.characters.ready">
                            ，缺少 {{ materialCheckResult.characters.missing }} 个头像
                          </template>
                        </el-tag>
                      </el-descriptions-item>
                      
                      <el-descriptions-item label="场景图">
                        <el-tag :type="materialCheckResult.sceneImages.ready ? 'success' : 'danger'">
                          {{ materialCheckResult.sceneImages.ready ? '✓' : '✗' }}
                          {{ materialCheckResult.sceneImages.total }} 个场景
                          <template v-if="!materialCheckResult.sceneImages.ready">
                            ，缺少 {{ materialCheckResult.sceneImages.missing }} 个场景图
                          </template>
                        </el-tag>
                      </el-descriptions-item>
                      
                      <el-descriptions-item label="关键帧">
                        <el-tag :type="materialCheckResult.keyframes.ready ? 'success' : 'danger'">
                          {{ materialCheckResult.keyframes.ready ? '✓' : '✗' }}
                          {{ materialCheckResult.keyframes.total }} 个分镜
                          <template v-if="!materialCheckResult.keyframes.ready">
                            ，缺少 {{ materialCheckResult.keyframes.missing }} 个关键帧
                          </template>
                        </el-tag>
                      </el-descriptions-item>
                      
                      <el-descriptions-item label="过渡视频">
                        <el-tag :type="materialCheckResult.transitions.ready ? 'success' : 'danger'">
                          {{ materialCheckResult.transitions.ready ? '✓' : '✗' }}
                          {{ materialCheckResult.transitions.total }} 个过渡
                          <template v-if="!materialCheckResult.transitions.ready">
                            ，缺少 {{ materialCheckResult.transitions.missing }} 个视频
                          </template>
                        </el-tag>
                      </el-descriptions-item>
                    </el-descriptions>
                    
                    <div style="margin-top: 20px; text-align: center;">
                      <el-button 
                        v-if="materialCheckResult.ready"
                        type="success" 
                        size="large"
                        @click="handleStartComposition"
                      >
                        <el-icon><VideoCamera /></el-icon>
                        开始合成电影
                      </el-button>
                      <el-alert
                        v-else
                        type="warning"
                        :closable="false"
                        show-icon
                      >
                        <template #title>
                          请先完成缺失的素材生成，然后重新检查
                        </template>
                      </el-alert>
                    </div>
                  </el-card>
                </el-space>
              </template>
            </el-result>
          </div>
        </div>
      </div>
    </div>

    <!-- 对话框组件 -->
    <StudioDialogs
      v-model:character-dialog="showCharacterDialog"
      v-model:scene-dialog="showSceneDialog"
      v-model:shot-dialog="showShotDialog"
      v-model:keyframe-dialog="showKeyframeDialog"
      v-model:transition-dialog="showTransitionDialog"
    />
    
    <!-- 章节编辑对话框 -->
    <ChapterFormDialog
      v-model="showChapterDialog"
      :chapter="editingChapter"
      @submit="handleChapterSubmit"
    />
    
    <!-- 电影合成对话框 -->
    <CreateMovieTaskDialog
      v-model="showMovieTaskDialog"
      :chapter-id="selectedChapterId"
      @success="handleCompositionSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoCamera } from '@element-plus/icons-vue'

import ChapterSelector from '@/components/studio/ChapterSelector.vue'
import WorkflowStepper from '@/components/studio/WorkflowStepper.vue'
import CharacterPanel from '@/components/studio/CharacterPanel.vue'
import ScenePanel from '@/components/studio/ScenePanel.vue'
import ShotPanel from '@/components/studio/ShotPanel.vue'
import SceneImagePanel from '@/components/studio/SceneImagePanel.vue'
import KeyframePanel from '@/components/studio/KeyframePanel.vue'
import TransitionPanel from '@/components/studio/TransitionPanel.vue'
import StudioDialogs from '@/components/studio/StudioDialogs.vue'
import ChapterFormDialog from '@/components/studio/ChapterFormDialog.vue'
import CreateMovieTaskDialog from '@/components/video/CreateMovieTaskDialog.vue'

import { useMovieWorkflow } from '@/composables/useMovieWorkflow'
import chaptersService from '@/services/chapters'

const route = useRoute()
const router = useRouter()

const {
  projectId,
  selectedChapterId,
  currentStep,
  loading,
  apiKeys,
  characterWorkflow,
  sceneWorkflow,
  shotWorkflow,
  transitionWorkflow,
  canExtractScenes,
  canExtractShots,
  canGenerateSceneImages,
  canGenerateKeyframes,
  canCreateTransitions,
  canGenerateTransitionVideos,
  loadData,
  goBack
} = useMovieWorkflow()

console.log('MovieStudio apiKeys from composable:', apiKeys.value)

// Dialog states
const showCharacterDialog = ref(false)
const showSceneDialog = ref(false)
const showShotDialog = ref(false)
const showKeyframeDialog = ref(false)
const showTransitionDialog = ref(false)
const showChapterDialog = ref(false)
const showMovieTaskDialog = ref(false)

// Chapter management
const editingChapter = ref(null)
const chapterSelectorRef = ref(null)

// Material check states
const checkingMaterials = ref(false)
const materialCheckResult = ref(null)

// Computed properties
const canExtractCharacters = computed(() => {
  return !!selectedChapterId.value
})

// Event handlers
const handleStepChange = (step) => {
  // 允许用户手动切换步骤，支持回退操作
  currentStep.value = step
}

const handleExtractCharacters = async (apiKeyId, model) => {
  // 角色提取直接使用chapter_id，不需要script
  if (!selectedChapterId.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  await characterWorkflow.extractCharacters(selectedChapterId.value, apiKeyId, model)
  await loadData()
}

const handleGenerateAvatar = async (characterId, apiKeyId, model, prompt, style, selectedReferenceIndices = []) => {
  await characterWorkflow.generateAvatar(characterId, apiKeyId, model, prompt, style, selectedReferenceIndices)
}

const handleDeleteCharacter = async (characterId) => {
  await characterWorkflow.deleteCharacter(characterId)
}

const handleBatchGenerateAvatars = async (apiKeyId, model) => {
  await characterWorkflow.batchGenerateAvatars(apiKeyId, model)
}

const handleExtractScenes = async (apiKeyId, model) => {
  if (!selectedChapterId.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  await sceneWorkflow.extractScenes(selectedChapterId.value, apiKeyId, model)
  await loadData(true)  // skipStepUpdate=true 保持当前步骤
}

const handleExtractShots = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await shotWorkflow.extractShots(sceneWorkflow.script.value.id, apiKeyId, model, sceneWorkflow.loadScript)
}

const handleExtractSingleSceneShots = async (sceneId, apiKeyId, model) => {
  await shotWorkflow.extractSingleSceneShots(sceneId, apiKeyId, model, sceneWorkflow.loadScript)
}


const handleBatchGenerateKeyframes = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await shotWorkflow.generateKeyframes(sceneWorkflow.script.value.id, apiKeyId, model, sceneWorkflow.loadScript)
}

const handleGenerateSingleKeyframe = async (shotId, apiKeyId, model, prompt) => {
  await shotWorkflow.generateSingleKeyframe(shotId, apiKeyId, model, prompt, sceneWorkflow.loadScript)
}

const handleBatchGenerateSceneImages = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await sceneWorkflow.generateSceneImages(sceneWorkflow.script.value.id, apiKeyId, model, sceneWorkflow.loadScript)
}

const handleGenerateSceneImage = async (sceneId, apiKeyId, model, prompt) => {
  await sceneWorkflow.generateSingleSceneImage(sceneId, apiKeyId, model, prompt, sceneWorkflow.loadScript)
}

const handleCreateTransitions = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await transitionWorkflow.createTransitions(sceneWorkflow.script.value.id, apiKeyId, model)
  await loadData(true)  // skipStepUpdate=true 保持当前步骤
}

const handleGenerateTransitionVideos = async (apiKeyId, videoModel) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await transitionWorkflow.generateTransitionVideos(sceneWorkflow.script.value.id, apiKeyId, videoModel)
  await loadData(true)  // skipStepUpdate=true 保持当前步骤
}

// Refresh handlers for history selection
const handleRefreshCharacters = async () => {
  await loadData(true)
}

const handleRefreshScenes = async () => {
  await sceneWorkflow.loadScript(selectedChapterId.value)
}

const handleRefreshKeyframes = async () => {
  await sceneWorkflow.loadScript(selectedChapterId.value)
}


// Material checking
const handleCheckMaterials = async () => {
  checkingMaterials.value = true
  materialCheckResult.value = null
  
  try {
    // 重新加载数据确保最新
    await loadData(true)
    
    // 检查各类素材
    const characters = characterWorkflow.characters.value || []
    const scenes = sceneWorkflow.script.value?.scenes || []
    const shots = shotWorkflow.sceneGroups.value.flatMap(g => g.shots) || []
    const transitions = transitionWorkflow.transitions.value || []
    
    // 统计缺失情况
    const missingCharacterAvatars = characters.filter(c => !c.avatar_url).length
    const missingSceneImages = scenes.filter(s => !s.scene_image_url).length
    const missingKeyframes = shots.filter(s => !s.keyframe_url).length
    const missingTransitionVideos = transitions.filter(t => !t.video_url).length
    
    materialCheckResult.value = {
      // 场景图不再是必需的，只要有角色头像、关键帧和过渡视频即可
      ready: missingCharacterAvatars === 0 && 
             missingKeyframes === 0 &&
             missingTransitionVideos === 0,
      characters: {
        total: characters.length,
        missing: missingCharacterAvatars,
        ready: missingCharacterAvatars === 0
      },
      sceneImages: {
        total: scenes.length,
        missing: missingSceneImages,
        ready: missingSceneImages === 0
      },
      keyframes: {
        total: shots.length,
        missing: missingKeyframes,
        ready: missingKeyframes === 0
      },
      transitions: {
        total: transitions.length,
        missing: missingTransitionVideos,
        ready: missingTransitionVideos === 0
      }
    }
    
    if (materialCheckResult.value.ready) {
      ElMessage.success('所有素材已准备就绪！')
      
      // 调用后端API更新章节状态为 materials_prepared
      if (selectedChapterId.value) {
        try {
          const api = await import('@/services/api')
          await api.default.put(`/chapters/${selectedChapterId.value}/update-status`, null, {
            params: { new_status: 'materials_prepared' }
          })
          console.log('章节状态已更新为 materials_prepared')
        } catch (error) {
          console.error('更新章节状态失败:', error)
          // 即使状态更新失败,也不影响用户继续操作
        }
      }
    } else {
      ElMessage.warning('部分素材缺失，请查看详情')
    }
  } catch (error) {
    console.error('检查素材失败:', error)
    ElMessage.error('检查素材失败: ' + (error.message || '未知错误'))
  } finally {
    checkingMaterials.value = false
  }
}

// Start composition
const handleStartComposition = () => {
  // 直接打开电影合成对话框
  showMovieTaskDialog.value = true
}

// Handle composition success
const handleCompositionSuccess = () => {
  ElMessage.success('电影合成任务已创建，可以在视频任务页面查看进度')
  // 可选：跳转到视频任务页面
  router.push({ name: 'GenerationPage' })
}

// Chapter management
const handleChapterCreate = () => {
  editingChapter.value = null
  showChapterDialog.value = true
}

const handleChapterSubmit = async (chapterData) => {
  try {
    if (chapterData.id) {
      // 编辑章节
      await chaptersService.updateChapter(chapterData.id, chapterData)
      ElMessage.success('章节更新成功')
    } else {
      // 创建章节
      await chaptersService.createChapter(projectId.value, chapterData)
      ElMessage.success('章节创建成功')
    }
    
    // 刷新章节列表
    if (chapterSelectorRef.value) {
      await chapterSelectorRef.value.fetchChapters()
    }
  } catch (error) {
    console.error('保存章节失败:', error)
    ElMessage.error('保存章节失败')
  }
}

// Watch projectId changes
watch(projectId, (newId) => {
  console.log('ProjectId changed:', newId)
  if (!newId) {
    ElMessage.warning('缺少项目ID，请从项目详情页进入')
  }
}, { immediate: true })
</script>

<style scoped>
.movie-studio-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.studio-sidebar-left {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border-right: 1px solid #e4e7ed;
  overflow: hidden;
}

.studio-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.studio-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 16px;
}

.studio-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.debug-info {
  margin-left: auto;
}

.studio-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-selection {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.workflow-content {
  max-width: 1400px;
  margin: 0 auto;
}

.final-step {
  padding: 60px 0;
}

.info-panel {
  background: white;
  border-radius: 8px;
  padding: 40px 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.material-check-card {
  max-width: 800px;
  margin: 0 auto;
}

.material-check-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
