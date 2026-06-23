<template>
  <div class="facility-grid">
    <div
      v-for="item in facilities"
      :key="item"
      class="facility-item"
    >
      <span class="facility-icon">{{ getIcon(item) }}</span>
      <span class="facility-label">{{ item }}</span>
    </div>

    <div v-if="!facilities.length" class="facility-empty">
      No facility information available yet
    </div>
  </div>
</template>

<script setup>
defineProps({
  facilities: { type: Array, default: () => [] },
})

const ICON_MAP = [
  { keys: ['wifi', 'wi-fi', '网络'], icon: '📶' },
  { keys: ['gym', '健身', '健身房'], icon: '🏋' },
  { keys: ['parking', '停车', 'park'], icon: '🚗' },
  { keys: ['airport', 'shuttle', '机场', '接机', '接送'], icon: '🚌' },
  { keys: ['breakfast', '早餐', '早饭'], icon: '☕' },
  { keys: ['pool', '泳池', '游泳池', 'swimming'], icon: '🏊' },
  { keys: ['air conditioning', '空调', '地暖', '暖', '冷气'], icon: '❄' },
  { keys: ['laundry', '洗衣机', '烘干', '洗衣', 'wash'], icon: '👕' },
  { keys: ['lock', '门锁', '智能', 'smart'], icon: '🔐' },
  { keys: ['luggage', '行李', 'baggage'], icon: '🧳' },
  { keys: ['toiletries', '洗漱', '一次性', '吹风机', 'amenities'], icon: '🧴' },
  { keys: ['front desk', '前台', 'reception', '24小时', '自助入住', 'check-in', 'self'], icon: '🛎' },
  { keys: ['tv', '电视', 'television'], icon: '📺' },
  { keys: ['kitchen', '厨房', 'kitchen'], icon: '🍳' },
  { keys: ['pets', '宠物', 'pet'], icon: '🐾' },
  { keys: ['smoking', '禁烟', '无烟', 'no smoking', 'non-smoking'], icon: '🚭' },
  { keys: ['elevator', '电梯', 'lift'], icon: '🛗' },
  { keys: ['garden', '花园', '庭院', 'garden'], icon: '🌿' },
  { keys: ['balcony', '阳台', '露台', 'terrace'], icon: '🏙' },
  { keys: ['heating', '暖气', 'heating'], icon: '🔥' },
]

const getIcon = (text) => {
  const lower = text.toLowerCase()
  for (const entry of ICON_MAP) {
    if (entry.keys.some(k => lower.includes(k))) {
      return entry.icon
    }
  }
  return '✨'
}
</script>

<style scoped>
.facility-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.facility-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 16px;
  background: rgba(255, 252, 247, 0.7);
  border: 1px solid rgba(128, 93, 72, 0.07);
  transition: all 0.2s ease;
}

.facility-item:hover {
  background: #fff;
  border-color: rgba(201, 134, 106, 0.2);
  box-shadow: 0 4px 16px rgba(201, 134, 106, 0.08);
  transform: translateY(-1px);
}

.facility-icon {
  font-size: 22px;
  flex-shrink: 0;
  line-height: 1;
}

.facility-label {
  font-size: 14px;
  color: #5c4a3a;
  font-weight: 500;
  line-height: 1.4;
}

.facility-empty {
  grid-column: 1 / -1;
  color: #aa9890;
  font-size: 14px;
  padding: 12px 0;
}
</style>
