<template>
  <div class="trust-strip">
    <div
      v-for="item in trustItems"
      :key="item.label"
      class="trust-item"
    >
      <span class="trust-item__icon">{{ item.icon }}</span>
      <span class="trust-item__label">{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup>
const trustItems = [
  { icon: '◆', label: 'Best Price Guarantee' },
  { icon: '↺', label: 'Free Cancellation' },
  { icon: '◈', label: '24/7 Support' },
  { icon: '◇', label: 'Secure Payment' },
]
</script>

<style scoped>
.trust-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
  padding: 28px 24px;
  background: rgba(20, 14, 10, 0.45);
  backdrop-filter: blur(12px);
}

.trust-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trust-item__icon {
  font-size: 12px;
  color: rgba(201, 134, 106, 0.75);
}

.trust-item__label {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.60);
  letter-spacing: 0.01em;
}

@media (max-width: 640px) {
  .trust-strip {
    gap: 20px;
    padding: 22px 16px;
  }

  .trust-item__label {
    font-size: 11px;
  }
}
</style>
