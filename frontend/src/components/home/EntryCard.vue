<template>
  <button
    class="entry-card"
    :class="`entry-card--${variant}`"
    @click="$emit('action')"
  >
    <!-- Icon -->
    <div class="entry-card__icon">
      <!-- Booking: Calendar -->
      <svg
        v-if="variant === 'booking'"
        width="24" height="24" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
      >
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
        <line x1="8" y1="14" x2="8" y2="14.01"/>
        <line x1="12" y1="14" x2="12" y2="14.01"/>
        <line x1="16" y1="14" x2="16" y2="14.01"/>
        <line x1="8" y1="18" x2="8" y2="18.01"/>
        <line x1="12" y1="18" x2="12" y2="18.01"/>
        <line x1="16" y1="18" x2="16" y2="18.01"/>
      </svg>
      <!-- AI: Sparkle -->
      <svg
        v-else
        width="24" height="24" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
      >
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    </div>

    <!-- Text -->
    <div class="entry-card__body">
      <h2 class="entry-card__title">{{ title }}</h2>
      <p class="entry-card__desc">{{ description }}</p>
    </div>

    <!-- CTA -->
    <span class="entry-card__cta" :class="`entry-card__cta--${variant}`">
      {{ actionText }}
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
    </span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'booking',
    validator: (v) => ['booking', 'ai'].includes(v),
  },
  title: { type: String, required: true },
  description: { type: String, required: true },
  actionText: { type: String, default: 'Get started' },
})
defineEmits(['action'])
</script>

<style scoped>
/* ═══════════════════════════════════════════════ */
/* GLASS CARD — floats on the hero image          */
/* ═══════════════════════════════════════════════ */
.entry-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  padding: 30px 32px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: all 0.4s ease;
  /* Frosted glass */
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.entry-card:hover {
  background: rgba(255, 255, 255, 0.13);
  border-color: rgba(255, 255, 255, 0.26);
  box-shadow:
    0 14px 40px rgba(0, 0, 0, 0.20),
    inset 0 1px 0 rgba(255, 255, 255, 0.10);
  transform: translateY(-2px);
}

/* Variant tints on hover */
.entry-card--booking:hover {
  background: rgba(201, 134, 106, 0.12);
  border-color: rgba(201, 134, 106, 0.32);
}

.entry-card--ai:hover {
  background: rgba(139, 164, 143, 0.12);
  border-color: rgba(139, 164, 143, 0.32);
}

/* ── Icon ── */
.entry-card__icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.10);
  transition: all 0.35s ease;
}

.entry-card:hover .entry-card__icon {
  transform: scale(1.06);
}

/* ── Text (white, over dark hero) ── */
.entry-card__body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entry-card__title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  line-height: 1.22;
  letter-spacing: -0.015em;
}

.entry-card__desc {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.60);
  line-height: 1.55;
  max-width: 300px;
}

/* ── CTA ── */
.entry-card__cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding: 10px 22px;
  border-radius: 13px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
  transition: all 0.25s ease;
}

.entry-card__cta--booking {
  background: rgba(201, 134, 106, 0.85);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}

.entry-card__cta--ai {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.25);
}

.entry-card:hover .entry-card__cta--booking {
  background: #c97a50;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.entry-card:hover .entry-card__cta--ai {
  background: rgba(255, 255, 255, 0.24);
  border-color: rgba(255, 255, 255, 0.40);
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .entry-card {
    padding: 22px 24px;
    gap: 12px;
  }

  .entry-card__title {
    font-size: 19px;
  }

  .entry-card__desc {
    font-size: 13px;
  }
}
</style>
