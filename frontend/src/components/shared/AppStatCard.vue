<template>
  <article class="stat-card fade-rise" :class="{ 'stat-card--loading': loading }">
    <div class="stat-card__head">
      <span class="stat-card__label">{{ label }}</span>
      <slot name="badge" />
    </div>
    <strong class="stat-card__value" :class="{ 'soft-skeleton': loading }">
      {{ value }}
    </strong>
    <p class="stat-card__desc" :class="{ 'soft-skeleton': loading }">
      {{ description }}
    </p>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  description: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 152px;
  padding: 20px;
  border-radius: 22px;
  border: 1px solid rgba(128, 93, 72, 0.12);
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 12px 26px rgba(114, 83, 60, 0.06);
}

.stat-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stat-card__label {
  color: var(--app-text-soft);
  font-size: 13px;
}

.stat-card__value {
  min-height: 42px;
  color: var(--app-text);
  font-size: clamp(28px, 4vw, 34px);
  line-height: 1.05;
}

.stat-card__desc {
  min-height: 22px;
  margin: 0;
  color: var(--app-text-soft);
  font-size: 13px;
  line-height: 1.7;
}

.stat-card--loading .stat-card__value,
.stat-card--loading .stat-card__desc {
  color: transparent;
  border-radius: 10px;
}
</style>
