<template>
  <div class="hotel-summary">
    <!-- Rating badge -->
    <div v-if="property.rating" class="summary-rating-badge">
      <span class="summary-stars">★</span>
      <span class="summary-rating-value">{{ property.rating }}</span>
      <span class="summary-rating-label">Exceptional</span>
    </div>

    <!-- Hotel Name -->
    <h1 class="summary-name">{{ property.propertyName }}</h1>

    <!-- Address -->
    <div class="summary-address">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="summary-address__icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
      <span>{{ property.city }} · {{ property.address }}</span>
    </div>

    <!-- Tags -->
    <div class="summary-tags">
      <span class="summary-tag">{{ typeText(property.propertyType) }}</span>
      <span v-if="property.availableRooms > 0" class="summary-tag summary-tag--success">
        {{ property.availableRooms }} rooms available
      </span>
      <span v-if="reviewCount" class="summary-tag summary-tag--ghost">
        {{ reviewCount }} reviews
      </span>
    </div>

    <!-- Check-in / Check-out -->
    <div class="summary-times">
      <div class="summary-time-block">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <div>
          <span class="summary-time-label">Check-in</span>
          <span class="summary-time-value">{{ property.checkInTime || '14:00' }}</span>
        </div>
      </div>
      <div class="summary-divider"></div>
      <div class="summary-time-block">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <div>
          <span class="summary-time-label">Check-out</span>
          <span class="summary-time-value">{{ property.checkOutTime || '12:00' }}</span>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="summary-actions">
      <button class="btn-book-now" @click="$emit('book')">
        Book Now
      </button>
      <button class="btn-icon-action" @click="$emit('favorite')" aria-label="Add to favorites">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      </button>
      <button class="btn-icon-action" @click="$emit('share')" aria-label="Share property">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  property: { type: Object, required: true },
  reviewCount: { type: Number, default: 0 },
})

defineEmits(['book', 'favorite', 'share'])

const typeText = (val) => {
  const map = {
    HOMESTAY: 'Homestay',
    HOTEL: 'Hotel',
    APARTMENT: 'Apartment',
    VILLA: 'Villa',
    OTHER: 'Other'
  }
  return map[val] || val || '-'
}
</script>

<style scoped>
.hotel-summary {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 8px 0;
}

/* ── Rating Badge ── */
.summary-rating-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  padding: 6px 16px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(201, 134, 106, 0.14), rgba(216, 164, 111, 0.16));
  border: 1px solid rgba(201, 134, 106, 0.18);
}

.summary-stars {
  font-size: 16px;
  color: #d6a45c;
}

.summary-rating-value {
  font-size: 15px;
  font-weight: 700;
  color: #3f312c;
}

.summary-rating-label {
  font-size: 13px;
  font-weight: 500;
  color: #7d6d66;
}

/* ── Hotel Name ── */
.summary-name {
  margin: 0;
  font-size: clamp(28px, 3.8vw, 42px);
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.015em;
  color: #3f312c;
}

/* ── Address ── */
.summary-address {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7d6d66;
  font-size: 14px;
  line-height: 1.5;
}

.summary-address__icon {
  flex-shrink: 0;
  color: #c9866a;
}

/* ── Tags ── */
.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  background: rgba(246, 237, 229, 0.7);
  color: #5c4a3a;
  border: 1px solid rgba(128, 93, 72, 0.1);
}

.summary-tag--success {
  background: rgba(139, 164, 143, 0.14);
  color: #5a7a5e;
  border-color: rgba(139, 164, 143, 0.24);
}

.summary-tag--ghost {
  background: rgba(255, 255, 255, 0.6);
  color: #7d6d66;
}

/* ── Check-in / Check-out Times ── */
.summary-times {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(255, 252, 247, 0.7);
  border: 1px solid rgba(128, 93, 72, 0.08);
}

.summary-time-block {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  color: #7d6d66;
}

.summary-time-block svg {
  flex-shrink: 0;
  color: #c9866a;
}

.summary-time-block > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-time-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #aa9890;
}

.summary-time-value {
  font-size: 16px;
  font-weight: 600;
  color: #3f312c;
}

.summary-divider {
  width: 1px;
  height: 36px;
  background: rgba(128, 93, 72, 0.14);
  margin: 0 20px;
}

/* ── Action Buttons ── */
.summary-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 4px;
}

.btn-book-now {
  flex: 1;
  padding: 16px 32px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #c97a50, #b56540);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: all 0.22s ease;
  box-shadow: 0 8px 22px rgba(168, 95, 71, 0.22);
}

.btn-book-now:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 32px rgba(168, 95, 71, 0.32);
  background: linear-gradient(135deg, #d0845a, #c06b42);
}

.btn-book-now:active {
  transform: translateY(0);
  box-shadow: 0 4px 14px rgba(168, 95, 71, 0.2);
}

.btn-icon-action {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  border: 1px solid rgba(128, 93, 72, 0.14);
  background: rgba(255, 255, 255, 0.72);
  color: #7d6d66;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-icon-action:hover {
  border-color: rgba(201, 134, 106, 0.4);
  color: #c9866a;
  background: #fff;
  box-shadow: 0 4px 16px rgba(201, 134, 106, 0.12);
}
</style>
