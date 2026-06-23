<template>
  <div class="stats-page">
    <PageIntro
      eyebrow="Operations Overview"
      title="把关键经营指标收束成一张更轻、更清楚的看板。"
      description="这里主要用于快速巡检。页面强调摘要、状态分布和当前风险，而不是复杂图表堆叠。"
    >
      <template #meta>
        <span class="app-pill">适合商户与管理员日常巡检</span>
        <span class="app-pill">使用当前接口实时聚合</span>
      </template>
    </PageIntro>

    <section class="stats-summary">
      <AppStatCard label="预订数量" :value="String(stats.bookings)" description="平台当前全部订单数量。" :loading="loading" />
      <AppStatCard label="民宿数量" :value="String(stats.properties)" description="已录入平台的房源总数。" :loading="loading" />
      <AppStatCard label="房型数量" :value="String(stats.roomTypes)" description="可供配置与售卖的房型总数。" :loading="loading" />
      <AppStatCard label="取消单" :value="String(stats.cancelled)" description="用于观察取消率与异常波动。" :loading="loading" />
    </section>

    <section class="stats-layout">
      <article class="status-panel app-section-card fade-rise">
        <div class="panel-head">
          <div>
            <p class="app-kicker">Status Mix</p>
            <h2>订单状态分布</h2>
          </div>
          <span class="app-pill">按当前数据计算</span>
        </div>

        <div v-if="statusStats.length" class="status-grid">
          <article v-for="item in statusStats" :key="item.name" class="status-item">
            <div class="status-item__head">
              <strong>{{ item.name }}</strong>
              <span>{{ item.count }} 单</span>
            </div>
            <el-progress
              :percentage="item.percent"
              :stroke-width="14"
              :show-text="false"
              :color="item.color"
            />
            <p>{{ item.description }}</p>
          </article>
        </div>
        <EmptyState
          v-else
          title="暂无状态数据"
          description="订单产生后，这里会显示不同状态的数量和占比。"
        />
      </article>

      <article class="insight-panel app-section-card fade-rise">
        <p class="app-kicker">Reading Notes</p>
        <h2>运营侧快速判断</h2>
        <div class="insight-list">
          <article class="insight-item">
            <strong>高频任务优先级</strong>
            <p>先关注待确认、待支付和取消单，再去处理房源与房型配置。</p>
          </article>
          <article class="insight-item">
            <strong>房源供给健康度</strong>
            <p>房源数和房型数接近时，说明可售结构还比较单一，后续可继续补充差异化房型。</p>
          </article>
          <article class="insight-item">
            <strong>取消率观察</strong>
            <p>取消订单异常升高时，优先排查支付体验、库存同步和时间选择流程。</p>
          </article>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageIntro from '../components/shared/PageIntro.vue'
import AppStatCard from '../components/shared/AppStatCard.vue'
import EmptyState from '../components/EmptyState.vue'
import { bookingApi, propertyApi, roomTypeApi } from '../api/index'
import { normalizeListResponse } from '../utils/media'

const loading = ref(false)
const stats = reactive({
  bookings: 0,
  properties: 0,
  roomTypes: 0,
  cancelled: 0,
  statusMap: {}
})

const statusMeta = {
  PENDING: { label: '待确认', color: '#d8a46f', description: '需要人工确认或等待系统继续推进。' },
  CONFIRMED: { label: '已确认', color: '#c9866a', description: '订单已确认，等待后续入住或支付环节。' },
  CHECKED_IN: { label: '已入住', color: '#8ba48f', description: '说明入住流程已经顺利发生。' },
  CHECKED_OUT: { label: '已退房', color: '#7d6d66', description: '完整闭环订单，可用于复盘整体体验。' },
  CANCELLED: { label: '已取消', color: '#c96f5e', description: '需要关注取消原因和频次变化。' },
  REFUNDED: { label: '已退款', color: '#9c8a7c', description: '关注退款链路是否稳定且可追溯。' }
}

const statusStats = computed(() => {
  const total = Object.values(stats.statusMap).reduce((a, b) => a + b, 0) || 1
  return Object.entries(stats.statusMap).map(([key, value]) => ({
    name: statusMeta[key]?.label || key,
    count: value,
    percent: Math.round((value / total) * 100),
    color: statusMeta[key]?.color || '#c9866a',
    description: statusMeta[key]?.description || '当前状态暂无额外说明。'
  }))
})

const loadData = async () => {
  loading.value = true
  try {
    const [bookingsRes, propertyRes, roomTypeRes] = await Promise.all([
      bookingApi.getList({}).catch(() => ({ data: [] })),
      propertyApi.getList({}).catch(() => ({ data: [] })),
      roomTypeApi.getList({}).catch(() => ({ data: [] }))
    ])

    const bookings = normalizeListResponse(bookingsRes)
    const properties = normalizeListResponse(propertyRes)
    const roomTypes = normalizeListResponse(roomTypeRes)

    stats.bookings = bookings.length
    stats.properties = properties.length
    stats.roomTypes = roomTypes.length
    stats.cancelled = bookings.filter((item) => item.status === 'CANCELLED').length
    stats.statusMap = bookings.reduce((acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1
      return acc
    }, {})
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.stats-page {
  display: grid;
  gap: 24px;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stats-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 22px;
}

.status-panel,
.insight-panel {
  padding: 24px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-head h2,
.insight-panel h2 {
  margin: 10px 0 0;
  font-size: 28px;
}

.status-grid,
.insight-list {
  display: grid;
  gap: 14px;
}

.status-item {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(128, 93, 72, 0.1);
  background: rgba(255, 255, 255, 0.68);
}

.status-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-item__head strong {
  color: var(--app-text);
}

.status-item__head span,
.status-item p,
.insight-item p {
  color: var(--app-text-soft);
  font-size: 13px;
  line-height: 1.75;
}

.status-item p,
.insight-item p {
  margin: 0;
}

.insight-item {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(128, 93, 72, 0.1);
}

.insight-item strong {
  display: block;
  margin-bottom: 8px;
  color: var(--app-text);
}

@media (max-width: 1200px) {
  .stats-summary,
  .stats-layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-summary,
  .stats-layout {
    grid-template-columns: 1fr;
  }

  .status-panel,
  .insight-panel {
    padding: 20px;
  }

  .panel-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
