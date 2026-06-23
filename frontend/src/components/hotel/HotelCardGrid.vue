<template>
  <div class="hotel-card-grid-container">
    <section
      v-for="category in categories"
      :key="category.name"
      class="hotel-category-section"
    >
      <div class="category-header">
        <div class="category-copy">
          <span class="category-pill">{{ category.name }}</span>
          <p class="category-meta">{{ category.hotels?.length || 0 }} 家推荐</p>
        </div>
      </div>

      <div class="hotel-card-grid" :class="{ 'hotel-card-grid--single': isSingleCategory(category) }">
        <article
          v-for="hotel in category.hotels"
          :key="hotel.id || hotel.propertyId || hotel.name"
          class="hotel-card"
        >
          <a
            class="hotel-card__media"
            :href="hotel.detailUrl || hotel.bookingUrl || '#'"
            target="_blank"
            rel="noreferrer"
          >
            <img :src="resolveImage(hotel.imageUrl)" :alt="hotel.name" loading="lazy" />
            <div class="hotel-card__overlay"></div>
            <div class="hotel-card__topbar">
              <span class="hotel-card__badge" :style="{ background: getCategoryColor(category.name) }">
                {{ hotel.badgeLabel || category.name }}
              </span>
              <span v-if="hotel.rating" class="hotel-card__rating">★ {{ hotel.rating }}</span>
            </div>
            <div class="hotel-card__price-chip" v-if="hotel.priceLabel || hotel.price">
              {{ hotel.priceLabel || hotel.price }}<small>/晚起</small>
            </div>
          </a>

          <div class="hotel-card__body">
            <div class="hotel-card__header">
              <h3 class="hotel-card__name">{{ hotel.name }}</h3>
              <p class="hotel-card__location">{{ hotel.location || hotel.address || '位置待确认' }}</p>
            </div>

            <p v-if="hotel.highlight" class="hotel-card__highlight">{{ hotel.highlight }}</p>

            <div v-if="hotel.tags?.length" class="hotel-card__tags">
              <span
                v-for="tag in hotel.tags.slice(0, 4)"
                :key="tag"
                class="hotel-card__tag"
              >
                {{ tag }}
              </span>
            </div>

            <div v-if="hotel.facilities?.length" class="hotel-card__facilities">
              <span
                v-for="facility in hotel.facilities.slice(0, 3)"
                :key="facility"
                class="hotel-card__facility"
              >
                {{ facility }}
              </span>
            </div>
          </div>

          <div class="hotel-card__footer">
            <a
              class="hotel-card__action hotel-card__action--ghost"
              :class="{ 'hotel-card__action--single': !(hotel.bookingUrl || hotel.detailUrl) }"
              :href="hotel.detailUrl || hotel.bookingUrl || '#'"
              target="_blank"
              rel="noreferrer"
            >
              {{ hotel.detailLabel || '查看详情' }}
            </a>
            <a
              class="hotel-card__action hotel-card__action--primary"
              :href="hotel.bookingUrl || hotel.detailUrl || '#'"
              target="_blank"
              rel="noreferrer"
            >
              {{ hotel.bookingLabel || '立即预订' }}
            </a>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
defineProps({
  categories: {
    type: Array,
    required: true
  }
})

const isSingleCategory = (category) => (Array.isArray(category?.hotels) ? category.hotels.length : 0) === 1

const FALLBACK_CARD_IMAGE =
  'data:image/svg+xml;charset=UTF-8,' +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#F3E7DE"/>
          <stop offset="100%" stop-color="#DDC0AE"/>
        </linearGradient>
      </defs>
      <rect width="640" height="480" fill="url(#g)"/>
      <g fill="none" stroke="#C58259" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" opacity="0.8">
        <rect x="184" y="154" width="272" height="180" rx="18"/>
        <path d="M214 334v-82h58v82M298 210h.01M344 210h.01M390 210h.01M298 250h.01M344 250h.01M390 250h.01"/>
      </g>
    </svg>
  `)

const categoryColors = {
  新开: 'linear-gradient(135deg, #0ea76b 0%, #067647 100%)',
  首选: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
  口岸: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
  高端: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
  奢华: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
  商务: 'linear-gradient(135deg, #6d55ff 0%, #4f46e5 100%)',
  亲子: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
  度假: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
  海景: 'linear-gradient(135deg, #0891b2 0%, #0f766e 100%)',
  默认: 'linear-gradient(135deg, #7c8ca0 0%, #556375 100%)'
}

const getCategoryColor = (categoryName = '') => {
  const key = Object.keys(categoryColors).find((item) => item !== '默认' && String(categoryName).includes(item))
  return categoryColors[key] || categoryColors.默认
}

const resolveImage = (value) => {
  if (!value || typeof value !== 'string') return FALLBACK_CARD_IMAGE
  const trimmed = value.trim()
  if (/^(https?:\/\/|data:image\/)/i.test(trimmed)) return trimmed
  if (trimmed.startsWith('/')) return `http://localhost:5400${trimmed}`
  if (/^(uploads|static)\//i.test(trimmed)) return `http://localhost:5400/${trimmed.replace(/^\/+/, '')}`
  return FALLBACK_CARD_IMAGE
}
</script>

<style scoped>
.hotel-card-grid-container {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.hotel-category-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.category-copy {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.category-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(201, 126, 86, 0.12);
  color: #9b5f3d;
  font-size: 12px;
  font-weight: 700;
}

.category-meta {
  margin: 0;
  font-size: 12px;
  color: #7d7168;
}

.hotel-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.hotel-card-grid--single {
  grid-template-columns: minmax(280px, 420px);
  justify-content: start;
}

.hotel-card {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  background: #fff;
  border: 1px solid rgba(155, 126, 105, 0.14);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(64, 46, 31, 0.06);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.hotel-card:hover {
  transform: translateY(-3px);
  border-color: rgba(201, 126, 86, 0.28);
  box-shadow: 0 20px 42px rgba(64, 46, 31, 0.12);
}

.hotel-card__media {
  position: relative;
  display: block;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: #eadfd7;
}

.hotel-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.35s ease;
}

.hotel-card:hover .hotel-card__media img {
  transform: scale(1.04);
}

.hotel-card__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(17, 17, 17, 0.08) 0%, rgba(17, 17, 17, 0.36) 100%);
}

.hotel-card__topbar {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.hotel-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(17, 17, 17, 0.14);
  max-width: 132px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hotel-card__rating {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #7a5419;
  font-size: 11px;
  font-weight: 700;
}

.hotel-card__price-chip {
  position: absolute;
  right: 12px;
  bottom: 12px;
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  color: #8f4f2f;
  font-size: 15px;
  font-weight: 800;
}

.hotel-card__price-chip small {
  font-size: 11px;
  font-weight: 600;
  color: #8f7a6a;
}

.hotel-card__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  flex: 1;
}

.hotel-card__header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hotel-card__name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.35;
  color: #241f1a;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hotel-card__location {
  margin: 0;
  font-size: 12.5px;
  color: #7d7168;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hotel-card__highlight {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #4a4139;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hotel-card__tags,
.hotel-card__facilities {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hotel-card__tag,
.hotel-card__facility {
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.hotel-card__tag {
  background: rgba(201, 126, 86, 0.12);
  color: #9b5f3d;
}

.hotel-card__facility {
  background: #f6f2ee;
  color: #6e6258;
}

.hotel-card__footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 0 16px 16px;
  margin-top: auto;
}

.hotel-card__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  border-radius: 12px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.hotel-card__action:hover {
  transform: translateY(-1px);
}

.hotel-card__action--ghost {
  border: 1px solid rgba(180, 145, 119, 0.28);
  background: #fff;
  color: #7c5538;
}

.hotel-card__action--primary {
  background: linear-gradient(140deg, #d9966f, #c97e56);
  color: #fff;
  box-shadow: 0 10px 18px rgba(201, 126, 86, 0.24);
}

@media (max-width: 640px) {
  .hotel-card-grid {
    grid-template-columns: 1fr;
  }

  .hotel-card-grid--single {
    grid-template-columns: 1fr;
  }

  .hotel-card__footer {
    grid-template-columns: 1fr;
  }
}
</style>
