<template>
  <div class="hotel-tabs">
    <el-tabs v-model="activeTab" class="custom-tabs">
      <!-- Tab: Overview -->
      <el-tab-pane label="Hotel Overview" name="overview">
        <div class="tab-content">
          <div class="overview-text" :class="{ 'overview-text--expanded': descExpanded }">
            <p>{{ property.description || 'No description available for this property yet.' }}</p>
          </div>
          <button
            v-if="needsExpand"
            class="overview-expand-btn"
            @click="descExpanded = !descExpanded"
          >
            {{ descExpanded ? 'Show less ▲' : 'Show more ▼' }}
          </button>

          <!-- Quick Facts -->
          <div v-if="quickFacts.length" class="overview-facts">
            <div v-for="fact in quickFacts" :key="fact.label" class="overview-fact">
              <span class="overview-fact__icon">{{ fact.icon }}</span>
              <div class="overview-fact__body">
                <span class="overview-fact__label">{{ fact.label }}</span>
                <span class="overview-fact__value">{{ fact.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab: Facilities -->
      <el-tab-pane label="Facilities" name="facilities">
        <div class="tab-content">
          <FacilityTags :facilities="facilities" />
        </div>
      </el-tab-pane>

      <!-- Tab: Policies -->
      <el-tab-pane label="Policies" name="policies">
        <div class="tab-content">
          <ul v-if="policies.length" class="policy-list">
            <li v-for="(item, i) in policies" :key="i" class="policy-item">
              <span class="policy-item__icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <span>{{ item }}</span>
            </li>
          </ul>
          <p v-else class="empty-text">No policy information available yet</p>
        </div>
      </el-tab-pane>

      <!-- Tab: Reviews -->
      <el-tab-pane label="Reviews" name="reviews">
        <div class="tab-content">
          <ReviewSection :rating="property.rating" :review-count="reviewCount" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import FacilityTags from './FacilityTags.vue'
import ReviewSection from './ReviewSection.vue'

const props = defineProps({
  property: { type: Object, required: true },
  facilities: { type: Array, default: () => [] },
  policies: { type: Array, default: () => [] },
  reviewCount: { type: Number, default: 126 },
})

const activeTab = ref('overview')
const descExpanded = ref(false)

const needsExpand = computed(() => {
  const desc = props.property?.description || ''
  return desc.length > 150
})

const quickFacts = computed(() => {
  const p = props.property || {}
  const facts = []
  if (p.propertyType) {
    facts.push({
      icon: '🏠',
      label: 'Property Type',
      value: typeText(p.propertyType),
    })
  }
  if (p.availableRooms != null) {
    facts.push({
      icon: '🛏',
      label: 'Available Rooms',
      value: `${p.availableRooms} rooms`,
    })
  }
  if (p.checkInTime) {
    facts.push({
      icon: '🕐',
      label: 'Check-in Time',
      value: p.checkInTime,
    })
  }
  if (p.checkOutTime) {
    facts.push({
      icon: '🕛',
      label: 'Check-out Time',
      value: p.checkOutTime,
    })
  }
  if (p.city) {
    facts.push({
      icon: '📍',
      label: 'City',
      value: p.city,
    })
  }
  return facts
})

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
.hotel-tabs {
  width: 100%;
}

/* ── Override Element Plus Tabs ── */
.custom-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.custom-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 600;
  color: #7d6d66;
  padding: 0 24px;
  height: 44px;
  line-height: 44px;
  transition: color 0.2s ease;
}

.custom-tabs :deep(.el-tabs__item:hover) {
  color: #c97a50;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #c97a50;
  font-weight: 700;
}

.custom-tabs :deep(.el-tabs__active-bar) {
  background: #c97a50;
  height: 3px;
  border-radius: 3px;
}

/* ── Tab Content ── */
.tab-content {
  min-height: 120px;
}

/* ── Overview ── */
.overview-text {
  position: relative;
}

.overview-text p {
  margin: 0;
  font-size: 15px;
  color: #5c4a3a;
  line-height: 1.8;
}

.overview-text:not(.overview-text--expanded) p {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.overview-expand-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  padding: 8px 0;
  border: none;
  background: none;
  color: #c97a50;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
}

.overview-expand-btn:hover {
  color: #a85f47;
}

/* ── Quick Facts ── */
.overview-facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid rgba(128, 93, 72, 0.08);
}

.overview-fact {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(255, 252, 247, 0.6);
  border: 1px solid rgba(128, 93, 72, 0.06);
}

.overview-fact__icon {
  font-size: 22px;
  flex-shrink: 0;
}

.overview-fact__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.overview-fact__label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #aa9890;
}

.overview-fact__value {
  font-size: 14px;
  font-weight: 600;
  color: #3f312c;
}

/* ── Policies ── */
.policy-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.policy-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 14px;
  font-size: 14px;
  color: #5c4a3a;
  line-height: 1.65;
  transition: background 0.2s ease;
}

.policy-item:hover {
  background: rgba(255, 252, 247, 0.6);
}

.policy-item__icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(139, 164, 143, 0.16);
  color: #8ba48f;
  display: grid;
  place-items: center;
  margin-top: 1px;
}

.empty-text {
  color: #aa9890;
  font-size: 14px;
  padding: 12px 0;
}
</style>
