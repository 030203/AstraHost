<template>
  <article class="room-card">
    <!-- Room Image -->
    <div class="room-card__image">
      <img
        :src="imageSrc"
        :alt="roomType.typeName"
        loading="lazy"
        @error="onImgError"
      />
      <span v-if="roomType.maxOccupancy" class="room-card__occupancy">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        Up to {{ roomType.maxOccupancy }}
      </span>
    </div>

    <!-- Room Info -->
    <div class="room-card__body">
      <div class="room-card__header">
        <h3 class="room-card__name">{{ roomType.typeName }}</h3>
        <div class="room-card__price">
          <span class="room-card__price-currency">¥</span>
          <span class="room-card__price-value">{{ displayPrice }}</span>
          <span class="room-card__price-unit">/ night</span>
        </div>
      </div>

      <!-- Details Row -->
      <div class="room-card__details">
        <div v-if="roomType.bedType" class="room-card__detail">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/></svg>
          {{ roomType.bedType }}
        </div>
        <div v-if="roomType.area" class="room-card__detail">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          {{ roomType.area }} m²
        </div>
      </div>

      <!-- Description -->
      <p v-if="roomType.description" class="room-card__desc">
        {{ roomType.description }}
      </p>

      <!-- Action -->
      <button class="room-card__book-btn" @click="$emit('book', roomType)">
        Book this room
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  roomType: { type: Object, required: true },
  index: { type: Number, default: 0 },
})

defineEmits(['book'])

const STATIC_IMAGES = [
  'https://pic.nximg.cn/20120414/128199_105320827000_2.jpg',
  'https://pic.nximg.cn/file/20200603/128199_102610317000_2.jpg'
]
const FALLBACK =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHgAAAB4CAYAAABV7bNHAAAACXBIWXMAAAsSAAALEgHS3X78AAAA/0lEQVR4nO3UsQkAIAwD0fb/6Z0lKpA12Nh4Jt9BxMyVAAAAAAAAAAAAAAAAAADgG7dwPZWf9g1tb29vHOU0A9nWZX1uHkCOVHrKeq8B6rD/XZTy/BFGMd0kRQz6kmoElSgzRFInknKQxSjbRFIvlkMojFKOtEUieSQxSNtEUi+WQyiMUo60RSJ5JDFI20RSL5ZD6KZJBWiySRWi6SVShtZCahd5L6pm2Q1kl2tqm4QmoXaS+qZtkNZJdrarpCaheJK9UeaFtJXaarpCahe5JaZ92NNVNdaKpCahfpJbJ83kDu6gZ0hW1d8kAAAAP//oAk/lKk3z8gAAAAASUVORK5CYII='

const parseImages = (val) => {
  if (!val) return []
  if (Array.isArray(val)) return val.filter(x => typeof x === 'string')
  try {
    const parsed = JSON.parse(val)
    return Array.isArray(parsed) ? parsed.filter(x => typeof x === 'string') : []
  } catch {
    if (typeof val === 'string' && val.startsWith('http')) return [val]
    return []
  }
}

const imageSrc = computed(() => {
  const imgs = parseImages(props.roomType?.images)
  if (imgs.length) return imgs[0]
  const pick = (props.roomType?.id != null ? Number(props.roomType.id) : props.index || 0) % STATIC_IMAGES.length
  return STATIC_IMAGES[pick]
})

const displayPrice = computed(() => {
  return Number(props.roomType?.basePrice || 0).toFixed(0)
})

const onImgError = (e) => {
  if (e.target && e.target.src !== FALLBACK) {
    e.target.src = FALLBACK
  }
}
</script>

<style scoped>
.room-card {
  border-radius: 22px;
  overflow: hidden;
  background: rgba(255, 253, 249, 0.85);
  border: 1px solid rgba(128, 93, 72, 0.08);
  box-shadow: 0 8px 28px rgba(114, 83, 60, 0.04);
  transition: all 0.28s ease;
  display: flex;
  flex-direction: column;
}

.room-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 44px rgba(114, 83, 60, 0.10);
  border-color: rgba(201, 134, 106, 0.2);
}

/* ── Image ── */
.room-card__image {
  position: relative;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: #f6ede5;
}

.room-card__image img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.room-card:hover .room-card__image img {
  transform: scale(1.04);
}

.room-card__occupancy {
  position: absolute;
  top: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

/* ── Body ── */
.room-card__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 22px 22px;
  flex: 1;
}

/* ── Header ── */
.room-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.room-card__name {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
  color: #3f312c;
  line-height: 1.3;
}

.room-card__price {
  display: flex;
  align-items: baseline;
  gap: 2px;
  flex-shrink: 0;
  text-align: right;
  line-height: 1;
}

.room-card__price-currency {
  font-size: 16px;
  font-weight: 600;
  color: #c97a50;
}

.room-card__price-value {
  font-size: 28px;
  font-weight: 800;
  color: #c97a50;
  letter-spacing: -0.01em;
}

.room-card__price-unit {
  font-size: 13px;
  font-weight: 500;
  color: #aa9890;
}

/* ── Details ── */
.room-card__details {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.room-card__detail {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #7d6d66;
}

.room-card__detail svg {
  color: #c9866a;
  flex-shrink: 0;
}

/* ── Description ── */
.room-card__desc {
  margin: 0;
  font-size: 14px;
  color: #7d6d66;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Book Button ── */
.room-card__book-btn {
  margin-top: auto;
  width: 100%;
  padding: 13px 20px;
  border: 2px solid #c97a50;
  border-radius: 14px;
  background: transparent;
  color: #c97a50;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.22s ease;
}

.room-card__book-btn:hover {
  background: #c97a50;
  color: #fff;
  box-shadow: 0 6px 18px rgba(201, 134, 106, 0.24);
  transform: translateY(-1px);
}

.room-card__book-btn:active {
  transform: translateY(0);
}
</style>
