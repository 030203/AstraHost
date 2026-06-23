<template>
  <div class="empty-state" :style="{ minHeight: height || '200px' }">
    <div class="empty-icon">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <h3 v-if="title">{{ title }}</h3>
    <h3 v-else>暂无数据</h3>
    <p v-if="description">{{ description }}</p>
    <p v-else>当前没有可显示的内容。</p>
    <slot name="action">
      <el-button v-if="actionText" type="primary" @click="$emit('action')">
        {{ actionText }}
      </el-button>
    </slot>
  </div>
</template>

<script setup>
import { FolderOpened } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  actionText: { type: String, default: '' },
  height: { type: String, default: '200px' },
  icon: { type: Object, default: () => FolderOpened }
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(201, 134, 106, 0.12), rgba(244, 215, 196, 0.26));
  display: grid;
  place-items: center;
  font-size: 34px;
  color: var(--app-primary-strong);
  margin-bottom: 8px;
}

.empty-state h3 {
  margin: 0;
  font-size: 18px;
  color: var(--app-text);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: var(--app-text-soft);
  line-height: 1.6;
  max-width: 400px;
  text-align: center;
}
</style>
