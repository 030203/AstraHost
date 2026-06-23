<template>
  <div class="hotel-gallery">
    <!-- Main Image -->
    <div class="gallery-main" @mouseenter="showArrows = true" @mouseleave="showArrows = false">
      <div
        class="gallery-main__image"
        :style="{ backgroundImage: `url(${currentImage})` }"
      >
        <!-- Image counter badge -->
        <span class="gallery-main__counter">
          {{ activeIndex + 1 }} / {{ images.length }}
        </span>
      </div>

      <!-- Prev / Next arrows -->
      <button
        v-if="showArrows && images.length > 1"
        class="gallery-arrow gallery-arrow--prev"
        @click="prev"
        aria-label="Previous image"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <button
        v-if="showArrows && images.length > 1"
        class="gallery-arrow gallery-arrow--next"
        @click="next"
        aria-label="Next image"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>

    <!-- Thumbnail Strip -->
    <div v-if="images.length > 1" class="gallery-thumbs">
      <button
        v-for="(img, idx) in images"
        :key="idx"
        class="gallery-thumb"
        :class="{ 'gallery-thumb--active': idx === activeIndex }"
        @click="activeIndex = idx"
        :aria-label="`View image ${idx + 1}`"
      >
        <img
          :src="img"
          :alt="`View ${idx + 1}`"
          loading="lazy"
          @error="onThumbError($event)"
        />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
})

const FALLBACK =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHgAAAB4CAYAAABV7bNHAAAACXBIWXMAAAsSAAALEgHS3X78AAAA/0lEQVR4nO3UsQkAIAwD0fb/6Z0lKpA12Nh4Jt9BxMyVAAAAAAAAAAAAAAAAAADgG7dwPZWf9g1tb29vHOU0A9nWZX1uHkCOVHrKeq8B6rD/XZTy/BFGMd0kRQz6kmoElSgzRFInknKQxSjbRFIvlkMojFKOtEUieSQxSNtEUi+WQyiMUo60RSJ5JDFI20RSL5ZD6KZJBWiySRWi6SVShtZCahd5L6pm2Q1kl2tqm4QmoXaS+qZtkNZJdrarpCaheJK9UeaFtJXaarpCahe5JaZ92NNVNdaKpCahfpJbJ83kDu6gZ0hW1d8kAAAAP//oAk/lKk3z8gAAAAASUVORK5CYII='

const activeIndex = ref(0)
const showArrows = ref(false)

const currentImage = computed(() => props.images[activeIndex.value] || FALLBACK)

const prev = () => {
  activeIndex.value = activeIndex.value === 0
    ? props.images.length - 1
    : activeIndex.value - 1
}

const next = () => {
  activeIndex.value = activeIndex.value === props.images.length - 1
    ? 0
    : activeIndex.value + 1
}

const onThumbError = (e) => {
  if (e.target && e.target.src !== FALLBACK) {
    e.target.src = FALLBACK
  }
}
</script>

<style scoped>
.hotel-gallery {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Main Image ── */
.gallery-main {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 24px;
  overflow: hidden;
  background: #f6ede5;
}

.gallery-main__image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: background-image 0.4s ease;
}

.gallery-main__counter {
  position: absolute;
  bottom: 16px;
  right: 16px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

/* ── Arrows ── */
.gallery-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  color: #3f312c;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  z-index: 2;
}

.gallery-arrow:hover {
  background: #fff;
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.14);
  transform: translateY(-50%) scale(1.06);
}

.gallery-arrow--prev { left: 14px; }
.gallery-arrow--next { right: 14px; }

/* ── Thumbnails ── */
.gallery-thumbs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}

.gallery-thumbs::-webkit-scrollbar { display: none; }

.gallery-thumb {
  flex-shrink: 0;
  width: 80px;
  height: 60px;
  border-radius: 14px;
  overflow: hidden;
  border: 2px solid transparent;
  padding: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #f6ede5;
  box-shadow: 0 2px 8px rgba(114, 83, 60, 0.05);
}

.gallery-thumb:hover {
  border-color: rgba(201, 134, 106, 0.4);
  box-shadow: 0 4px 14px rgba(114, 83, 60, 0.10);
}

.gallery-thumb--active {
  border-color: #c9866a;
  box-shadow: 0 4px 16px rgba(201, 134, 106, 0.24);
}

.gallery-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>
