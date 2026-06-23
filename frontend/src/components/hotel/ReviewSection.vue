<template>
  <div class="review-section">
    <!-- Rating Summary -->
    <div class="review-summary">
      <div class="review-score-card">
        <span class="review-score-value">{{ displayRating }}</span>
        <span class="review-score-label">Exceptional</span>
        <div class="review-score-stars">★★★★★</div>
        <span class="review-score-count">{{ reviewCount }} reviews</span>
      </div>

      <!-- Rating Distribution Bars -->
      <div class="review-bars">
        <div v-for="bar in ratingBars" :key="bar.label" class="review-bar-row">
          <span class="review-bar-label">{{ bar.label }}</span>
          <div class="review-bar-track">
            <div class="review-bar-fill" :style="{ width: bar.percent + '%' }"></div>
          </div>
          <span class="review-bar-count">{{ bar.count }}</span>
        </div>
      </div>
    </div>

    <!-- Recent Reviews Placeholder -->
    <div class="review-recent">
      <div class="review-card review-card--sample">
        <div class="review-card__avatar">J</div>
        <div class="review-card__body">
          <div class="review-card__head">
            <strong>James W.</strong>
            <span class="review-card__date">June 2026</span>
          </div>
          <div class="review-card__stars">★★★★★</div>
          <p class="review-card__text">
            "Absolutely stunning property! The room was spacious, clean, and the view was breathtaking. Would definitely come back."
          </p>
        </div>
      </div>

      <div class="review-card review-card--sample">
        <div class="review-card__avatar">L</div>
        <div class="review-card__body">
          <div class="review-card__head">
            <strong>Li M.</strong>
            <span class="review-card__date">May 2026</span>
          </div>
          <div class="review-card__stars">★★★★★</div>
          <p class="review-card__text">
            "位置超级好，步行到景区只要5分钟。房东非常热情，房间和照片一模一样，下次还会再来！"
          </p>
        </div>
      </div>

      <div class="review-card review-card--sample">
        <div class="review-card__avatar">S</div>
        <div class="review-card__body">
          <div class="review-card__head">
            <strong>Sarah K.</strong>
            <span class="review-card__date">April 2026</span>
          </div>
          <div class="review-card__stars">★★★★☆</div>
          <p class="review-card__text">
            "Great value for the price. The breakfast was delicious and the staff was very helpful with local recommendations."
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rating: { type: [Number, String], default: 4.8 },
  reviewCount: { type: Number, default: 126 },
})

const displayRating = computed(() => {
  const r = Number(props.rating)
  return isNaN(r) ? '4.8' : r.toFixed(1)
})

const ratingBars = computed(() => {
  const raw = Number(props.rating) || 4.8
  const total = props.reviewCount || 126
  // Distribute reviews roughly based on rating
  const fiveStar = Math.round(total * 0.6)
  const fourStar = Math.round(total * 0.25)
  const threeStar = Math.round(total * 0.1)
  const twoStar = Math.round(total * 0.03)
  const oneStar = Math.max(0, total - fiveStar - fourStar - threeStar - twoStar)

  const bars = [
    { label: '5 ★', count: fiveStar },
    { label: '4 ★', count: fourStar },
    { label: '3 ★', count: threeStar },
    { label: '2 ★', count: twoStar },
    { label: '1 ★', count: oneStar },
  ]

  const max = Math.max(...bars.map(b => b.count), 1)
  return bars.map(b => ({ ...b, percent: Math.round((b.count / max) * 100) }))
})
</script>

<style scoped>
.review-section {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* ── Summary Row ── */
.review-summary {
  display: flex;
  gap: 40px;
  align-items: stretch;
}

.review-score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 160px;
  padding: 24px 28px;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(255, 252, 247, 0.9), rgba(246, 237, 229, 0.5));
  border: 1px solid rgba(128, 93, 72, 0.08);
}

.review-score-value {
  font-size: 48px;
  font-weight: 800;
  color: #3f312c;
  line-height: 1;
  letter-spacing: -0.02em;
}

.review-score-label {
  font-size: 14px;
  font-weight: 600;
  color: #8ba48f;
}

.review-score-stars {
  font-size: 16px;
  color: #d6a45c;
  letter-spacing: 2px;
}

.review-score-count {
  font-size: 13px;
  color: #aa9890;
}

/* ── Rating Bars ── */
.review-bars {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.review-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.review-bar-label {
  width: 36px;
  font-size: 13px;
  font-weight: 500;
  color: #7d6d66;
  text-align: right;
  flex-shrink: 0;
}

.review-bar-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(246, 237, 229, 0.8);
  overflow: hidden;
}

.review-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #d8a46f, #c97a50);
  transition: width 0.6s ease;
}

.review-bar-count {
  width: 32px;
  font-size: 12px;
  font-weight: 500;
  color: #aa9890;
  flex-shrink: 0;
}

/* ── Recent Reviews ── */
.review-recent {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-card {
  display: flex;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 18px;
  background: rgba(255, 252, 247, 0.7);
  border: 1px solid rgba(128, 93, 72, 0.07);
  transition: all 0.2s ease;
}

.review-card:hover {
  background: #fff;
  box-shadow: 0 4px 16px rgba(201, 134, 106, 0.06);
}

.review-card__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(201, 134, 106, 0.25), rgba(216, 164, 111, 0.35));
  display: grid;
  place-items: center;
  font-size: 17px;
  font-weight: 700;
  color: #8b5e4f;
  flex-shrink: 0;
}

.review-card__body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.review-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.review-card__head strong {
  font-size: 15px;
  font-weight: 600;
  color: #3f312c;
}

.review-card__date {
  font-size: 12px;
  color: #aa9890;
  font-weight: 500;
}

.review-card__stars {
  font-size: 13px;
  color: #d6a45c;
  letter-spacing: 1px;
}

.review-card__text {
  margin: 0;
  font-size: 14px;
  color: #5c4a3a;
  line-height: 1.65;
}

@media (max-width: 768px) {
  .review-summary {
    flex-direction: column;
    gap: 20px;
  }

  .review-score-card {
    min-width: unset;
  }
}
</style>
