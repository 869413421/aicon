<template>
  <div class="workflow-stepper">
    <el-steps :active="currentStep" align-center finish-status="success">
      <el-step 
        v-for="(step, index) in steps" 
        :key="index"
        :title="step.title"
        :description="step.description"
        :icon="step.icon"
        @click="handleStepClick(index)"
        class="clickable-step"
      />
    </el-steps>
  </div>
</template>

<script setup>
import { VideoCamera, Film, Camera, Picture, Connection, Check } from '@element-plus/icons-vue'

const props = defineProps({
  currentStep: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['change-step'])

const steps = [
  {
    title: '角色管理',
    description: '提取角色并生成定妆照',
    icon: VideoCamera
  },
  {
    title: '场景提取',
    description: '从章节提取场景',
    icon: Film
  },
  {
    title: '分镜提取',
    description: '为场景生成分镜',
    icon: Camera
  },
  {
    title: '场景图生成',
    description: '生成场景环境参考图',
    icon: Picture
  },
  {
    title: '关键帧生成',
    description: '生成分镜关键帧图片',
    icon: Picture
  },
  {
    title: '过渡视频',
    description: '生成分镜间过渡视频',
    icon: Connection
  },
  {
    title: '最终合成',
    description: '合成完整电影',
    icon: Check
  }
]

const handleStepClick = (index) => {
  // 允许用户点击任何步骤进行回退或跳转
  emit('change-step', index)
}
</script>

<style scoped>
.workflow-stepper {
  padding: 24px;
  background: white;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

:deep(.el-step__title) {
  font-size: 14px;
  font-weight: 600;
}

:deep(.el-step__description) {
  font-size: 12px;
}

.clickable-step {
  cursor: pointer;
}

.clickable-step:hover :deep(.el-step__title) {
  color: #409eff;
}
</style>
