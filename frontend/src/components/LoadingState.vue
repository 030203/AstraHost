<template>
  <div class="loading-state" :style="{ minHeight: height || '200px' }">
    <div class="loading-spinner">
      <div class="spinner-ring"></div>
      <div class="spinner-ring spinner-ring--inner"></div>
    </div>
    <p v-if="text" class="loading-text">{{ text }}</p>
    <p v-else class="loading-text">加载中，请稍候...</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '' },
  height: { type: String, default: '200px' }
})
</script>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
}

.loading-spinner {
  position: relative;
  width: 52px;
  height: 52px;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid rgba(201, 134, 106, 0.14);
  border-top-color: var(--app-primary);
  animation: spin 0.8s linear infinite;
}

.spinner-ring--inner {
  inset: 8px;
  border-width: 3px;
  border-top-color: var(--app-secondary);
  animation-direction: reverse;
  animation-duration: 0.6s;
}

.loading-text {
  margin: 0;
  color: var(--app-text-soft);
  font-size: 14px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
