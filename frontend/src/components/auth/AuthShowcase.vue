<template>
  <section class="auth-showcase">
    <div class="auth-showcase__copy">
      <p class="app-kicker">{{ eyebrow }}</p>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>

    <div class="auth-showcase__list">
      <article v-for="item in items" :key="item.title" class="auth-showcase__item">
        <div class="auth-showcase__icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <div>
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  items: { type: Array, default: () => [] }
})
</script>

<style scoped>
.auth-showcase {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 30px;
  min-height: 100%;
  padding: 42px;
  color: #fffaf6;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.18), transparent 24%),
    radial-gradient(circle at 82% 14%, rgba(255, 240, 227, 0.18), transparent 26%),
    linear-gradient(150deg, #8f4f38 0%, #c9866a 46%, #e5ba8d 100%);
}

.auth-showcase__copy h2 {
  margin: 12px 0 14px;
  font-size: 36px;
  line-height: 1.08;
}

.auth-showcase__copy p:last-child {
  margin: 0;
  color: rgba(255, 250, 246, 0.88);
  line-height: 1.8;
}

.auth-showcase__list {
  display: grid;
  gap: 14px;
}

.auth-showcase__item {
  display: flex;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(6px);
}

.auth-showcase__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
  flex-shrink: 0;
  font-size: 18px;
}

.auth-showcase__item strong {
  display: block;
  margin-bottom: 6px;
}

.auth-showcase__item p {
  margin: 0;
  color: rgba(255, 250, 246, 0.86);
  font-size: 14px;
  line-height: 1.65;
}

@media (max-width: 980px) {
  .auth-showcase {
    padding: 28px;
  }

  .auth-showcase__copy h2 {
    font-size: 30px;
  }
}
</style>
