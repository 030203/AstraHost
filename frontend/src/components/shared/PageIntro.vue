<template>
  <section class="page-intro app-section-card fade-rise">
    <div class="page-intro__copy">
      <p v-if="eyebrow" class="app-kicker">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p v-if="description" class="page-intro__description">
        {{ description }}
      </p>
      <div v-if="$slots.meta" class="page-intro__meta">
        <slot name="meta" />
      </div>
    </div>
    <div v-if="$slots.actions" class="page-intro__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.page-intro {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
}

.page-intro__copy {
  max-width: 780px;
}

.page-intro h1 {
  margin: 10px 0 12px;
  color: var(--app-text);
  font-size: clamp(30px, 4vw, 42px);
  line-height: 1.08;
}

.page-intro__description {
  margin: 0;
  color: var(--app-text-soft);
  font-size: 15px;
  line-height: 1.8;
}

.page-intro__meta {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.page-intro__actions {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .page-intro {
    flex-direction: column;
    padding: 22px;
  }

  .page-intro__actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .page-intro__actions :deep(.el-button) {
    flex: 1 1 180px;
  }
}
</style>
