<template>
  <div class="movie-studio-layout">
    <!-- 侧边栏：章节选择 -->
    <div class="studio-sidebar-left">
      <ChapterSelector 
        v-model="selectedChapterId" 
        :project-id="projectId"
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
            :can-extract="canExtractCharacters"
            :api-keys="apiKeys"
            @extract-characters="handleExtractCharacters"
            @generate-avatar="handleGenerateAvatar"
            @delete-character="handleDeleteCharacter"
            @batch-generate="handleBatchGenerateAvatars"
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
            :can-extract="canExtractShots"
            :api-keys="apiKeys"
            @extract-shots="handleExtractShots"
          />

          <!-- 步骤3: 场景图生成 -->
          <SceneImagePanel
            v-show="currentStep === 3"
            :scenes="sceneWorkflow.script.value?.scenes || []"
            :can-generate="canGenerateSceneImages"
            :api-keys="apiKeys"
            :generating-ids="sceneWorkflow.generatingSceneImages.value"
            @batch-generate="handleBatchGenerateSceneImages"
            @generate-scene-image="handleGenerateSceneImage"
          />

          <!-- 步骤4: 关键帧生成 -->
          <KeyframePanel
            v-show="currentStep === 4"
            :scene-groups="shotWorkflow.sceneGroups.value"
            :can-generate="canGenerateKeyframes"
            :api-keys="apiKeys"
            :generating-ids="shotWorkflow.generatingKeyframes.value"
            @batch-generate="handleBatchGenerateKeyframes"
            @generate-keyframe="handleGenerateSingleKeyframe"
          />

          <!-- 步骤5: 过渡视频 -->
          <TransitionPanel
            v-show="currentStep === 5"
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
              sub-title="可以开始最终合成了"
            >
              <template #extra>
                <el-button type="primary" size="large">开始合成</el-button>
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
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

import ChapterSelector from '@/components/studio/ChapterSelector.vue'
import WorkflowStepper from '@/components/studio/WorkflowStepper.vue'
import CharacterPanel from '@/components/studio/CharacterPanel.vue'
import ScenePanel from '@/components/studio/ScenePanel.vue'
import ShotPanel from '@/components/studio/ShotPanel.vue'
import SceneImagePanel from '@/components/studio/SceneImagePanel.vue'
import KeyframePanel from '@/components/studio/KeyframePanel.vue'
import TransitionPanel from '@/components/studio/TransitionPanel.vue'
import StudioDialogs from '@/components/studio/StudioDialogs.vue'

import { useMovieWorkflow } from '@/composables/useMovieWorkflow'

const route = useRoute()

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

const handleGenerateAvatar = async (characterId, apiKeyId, model, prompt, style) => {
  await characterWorkflow.generateAvatar(characterId, apiKeyId, model, prompt, style)
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
  await shotWorkflow.extractShots(sceneWorkflow.script.value.id, apiKeyId, model)
  await loadData(true)  // skipStepUpdate=true 保持当前步骤
}

const handleBatchGenerateKeyframes = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await shotWorkflow.generateKeyframes(sceneWorkflow.script.value.id, apiKeyId, model)
  await loadData(true)
}

const handleGenerateSingleKeyframe = async (shotId, apiKeyId, model, prompt) => {
  await shotWorkflow.generateSingleKeyframe(shotId, apiKeyId, model, prompt)
  await loadData(true)
}

const handleBatchGenerateSceneImages = async (apiKeyId, model) => {
  if (!sceneWorkflow.script.value?.id) {
    ElMessage.warning('请先提取场景')
    return
  }
  await sceneWorkflow.generateSceneImages(sceneWorkflow.script.value.id, apiKeyId, model)
  await loadData(true)
}

const handleGenerateSceneImage = async (sceneId, apiKeyId, model, prompt) => {
  await sceneWorkflow.generateSingleSceneImage(sceneId, apiKeyId, model, prompt)
  await loadData(true)
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
</style>
