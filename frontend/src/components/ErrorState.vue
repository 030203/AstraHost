<template>
  <div class="error-state" :style="{ minHeight: height || '200px' }">
    <div class="error-icon">
      <el-icon><WarningFilled /></el-icon>
    </div>
    <h3 v-if="title">{{ title }}</h3>
    <h3 v-else>加载失败</h3>
    <p v-if="message">{{ message }}</p>
    <p v-else>数据加载出错，请稍后重试。</p>
    <div class="error-actions">
      <el-button v-if="retryText" type="primary" @click="$emit('retry')">
        <el-icon><Refresh /></el-icon>
        {{ retryText }}
      </el-button>
      <el-button v-else type="primary" @click="$emit('retry')">
        <el-icon><Refresh /></el-icon>
        重试
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { WarningFilled, Refresh } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  retryText: { type: String, default: '' },
  height: { type: String, default: '200px' }
})

defineEmits(['retry'])
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
}

.error-icon {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: rgba(201, 111, 94, 0.12);
  display: grid;
  place-items: center;
  font-size: 34px;
  color: var(--app-danger);
  margin-bottom: 8px;
}

.error-state h3 {
  margin: 0;
  font-size: 18px;
  color: var(--app-text);
}

.error-state p {
  margin: 0;
  font-size: 14px;
  color: var(--app-text-soft);
  line-height: 1.6;
  max-width: 440px;
  text-align: center;
}

.error-actions {
  margin-top: 8px;
}

.error-actions .el-button span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
