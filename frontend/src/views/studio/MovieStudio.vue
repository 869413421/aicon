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
      <MovieHeader
        :chapter="chapter"
        :script="script"
        :completion-status="completionStatus"
        :checking-completion="checkingCompletion"
        :can-prepare-materials="canPrepareMaterials"
        :gen-config="genConfig"
        :api-keys="apiKeys"
        :show-cast-manager="showCastManager"
        :loading-keyframes="generatingKeyframes"
        :batch-producing="batchProducing"
        :all-charactersReady="allCharactersReady"
        :loading-script="generatingScript"
        :is-polling="isPolling"
        :task-status="taskStatus"
        :task-statistics="taskStatistics"
        :task-result="taskResult"
        @back="goBack"
        @check-completion="checkCompletion"
        @prepare-materials="handlePrepareMaterials"
        @update-api-key="(val) => { genConfig.api_key_id = val; fetchModels() }"
        @toggle-cast="showCastManager = !showCastManager"
        @generate-keyframes="handleGenerateKeyframes"
        @produce-batch="handleBatchProduceVideos"
        @generate-script="handleGenerateScript"
        @terminate="terminateTask"
      />

      <!-- 内容区 -->
      <div class="studio-body">
        <div class="studio-content" v-loading="isPolling" element-loading-text="AI正在创作中，请稍候...">
          
          <div v-if="!chapter && !loading" class="empty-selection">
            <el-empty description="请从左侧选择一个章节开始制作" />
          </div>

          <div v-else-if="loading" class="studio-skeleton">
            <el-skeleton :rows="10" animated />
          </div>

          <!-- 脚本看板 -->
          <SceneList
            v-else-if="script"
            :script="script"
            :show-video="showVideo"
            :characters="characters"
            @toggle-view="toggleShotView"
            @produce-shot="handleProduceShot"
            @shot-command="handleShotCommand"
            @update-prompt="handleUpdateShotPrompt"
          />
  
          <div v-else-if="!loading" class="empty-state">
            <el-empty description="当前章节暂无剧本">
              <el-button type="primary" @click="handleGenerateScript">生成 AI 剧本</el-button>
            </el-empty>
          </div>
        </div>
        
        <!-- 右侧剧组栏 -->
        <transition name="slide-fade">
          <CastManager
            v-if="showCastManager"
            :characters="characters"
            :extracting="extractingCharacters"
            @detect="handleDetectCharacters"
            @generate-avatar="handleGenerateAvatar"
            @delete-character="handleDeleteCharacter"
            @batch-generate="handleBatchGenerateAvatars"
          />
        </transition>
      </div>
    </div>

    <!-- 弹窗容器 -->
    <StudioDialogs
      v-model:visible="showGenerateDialog"
      v-model:genConfig="genConfig"
      :mode="dialogMode"
      :api-keys="apiKeys"
      :model-options="modelOptions"
      :loading-models="loadingModels"
      :loading="generatingScript || extractingCharacters || !!generatingAvatarId || generatingKeyframes"
      @confirm="handleDialogConfirm"
    />
  </div>
</template>

<script setup>
import { useMovieStudio } from '@/composables/useMovieStudio'
import ChapterSelector from '@/components/studio/ChapterSelector.vue'
import MovieHeader from '@/components/studio/MovieHeader.vue'
import CastManager from '@/components/studio/CastManager.vue'
import SceneList from '@/components/studio/SceneList.vue'
import StudioDialogs from '@/components/studio/StudioDialogs.vue'

const {
  selectedChapterId, projectId, chapter, script, characters, apiKeys,
  loading, generatingScript, extractingCharacters, generatingKeyframes,
  batchProducing, generatingAvatarId, showCastManager,
  showGenerateDialog, dialogMode, modelOptions, loadingModels,
  showVideo, completionStatus, checkingCompletion,
  genConfig, isPolling,
  canPrepareMaterials, allCharactersReady,
  fetchModels, handleGenerateScript, confirmGenerate,
  handleDetectCharacters, confirmExtractCharacters, handleGenerateAvatar, confirmAvatar,
  handleDeleteCharacter, handleBatchGenerateAvatars, confirmBatchGenerateAvatars,
  handleGenerateKeyframes, confirmKeyframes, handleProduceShot,
  confirmProduceSingle, handleBatchProduceVideos, confirmProduceBatch,
  handlePrepareMaterials, handleRegenerateKeyframe, handleRegenerateLastFrame,
  handleRegenerateVideo, toggleShotView, goBack, handleShotCommand,
  checkCompletion, handleUpdateShotPrompt, taskStatus, taskStatistics, taskResult
} = useMovieStudio()

const handleDialogConfirm = () => {
  if (dialogMode.value === 'script') confirmGenerate()
  else if (dialogMode.value === 'character') confirmExtractCharacters()
  else if (dialogMode.value === 'keyframes') confirmKeyframes()
  else if (dialogMode.value === 'produce-single') confirmProduceSingle()
  else if (dialogMode.value === 'produce-batch') confirmProduceBatch()
  else if (dialogMode.value === 'batch-avatars') confirmBatchGenerateAvatars()
  else if (dialogMode.value === 'regen-keyframe') handleRegenerateKeyframe()
  else if (dialogMode.value === 'regen-last-frame') handleRegenerateLastFrame()
  else if (dialogMode.value === 'regen-video') handleRegenerateVideo()
  else confirmAvatar()
}
</script>

<style scoped>
.movie-studio-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.studio-sidebar-left {
  width: 250px;
  flex-shrink: 0;
  height: 100%;
}

.studio-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f7fa;
}

.studio-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.studio-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  position: relative;
}

.empty-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease-out;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
