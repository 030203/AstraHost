<template>
  <div class="qb-page">
    <!-- Compact hero with inline search -->
    <section class="qb-hero fade-rise">
      <div class="qb-hero__inner">
        <p class="qb-hero__eyebrow">QUICK BOOKING</p>
        <h1 class="qb-hero__title">发现值得入住的优质房源</h1>
        <p class="qb-hero__subtitle">搜索城市、日期和人数，快速完成预订</p>

        <div class="qb-search">
          <div class="qb-search__field">
            <label>目的地</label>
            <el-input
              v-model="filters.city"
              placeholder="想去哪座城市？"
              :prefix-icon="LocationFilled"
              @keyup.enter="applyFilters"
            />
          </div>
          <span class="qb-search__sep"></span>
          <div class="qb-search__field qb-search__field--dates">
            <label>入住 / 离店</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              start-placeholder="入住"
              end-placeholder="离店"
              :prefix-icon="Calendar"
            />
          </div>
          <span class="qb-search__sep"></span>
          <div class="qb-search__field">
            <label>入住人数</label>
            <el-select v-model="form.numberOfGuests" :prefix-icon="User">
              <el-option v-for="n in 10" :key="n" :label="`${n} 位房客`" :value="n" />
            </el-select>
          </div>
          <el-button type="primary" class="qb-search__btn" :icon="Search" @click="applyFilters">
            搜索
          </el-button>
        </div>
      </div>
    </section>

    <!-- Popular destinations -->
    <section class="qb-chips fade-rise">
      <span class="qb-chips__label">热门目的地</span>
      <div class="qb-chips__row">
        <button
          v-for="city in popularCities"
          :key="city"
          class="qb-chip"
          :class="{ 'qb-chip--active': filters.city === city }"
          @click="quickCity(city)"
        >
          {{ city }}
        </button>
        <button v-if="filters.city || filters.keyword" class="qb-chip qb-chip--reset" @click="resetFilter">
          清除筛选
        </button>
      </div>
    </section>

    <!-- Main two-column layout -->
    <section class="qb-main">
      <!-- LEFT: discovery -->
      <div class="qb-discovery">
        <div class="qb-discovery__head">
          <div>
            <h2>{{ filters.city ? `${filters.city} · 精选房源` : '为你精选的房源' }}</h2>
            <p>{{ loading ? '正在加载…' : `共 ${total} 套房源 · 第 ${currentPage} / ${totalPages} 页` }}</p>
          </div>
          <el-select v-model="filters.minRating" placeholder="评分排序" clearable class="qb-discovery__sort" @change="applyFilters">
            <el-option v-for="o in ratingOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </div>

        <!-- Skeleton -->
        <div v-if="loading" class="qb-grid">
          <div v-for="n in 6" :key="n" class="qb-card qb-card--skeleton">
            <div class="qb-card__media soft-skeleton"></div>
            <div class="qb-card__body">
              <div class="soft-skeleton sk-line sk-line--lg"></div>
              <div class="soft-skeleton sk-line"></div>
              <div class="soft-skeleton sk-line sk-line--sm"></div>
            </div>
          </div>
        </div>

        <!-- Cards -->
        <div v-else-if="properties.length" class="qb-grid">
          <article
            v-for="(item, index) in properties"
            :key="item.id"
            class="qb-card"
            :class="{ 'qb-card--active': form.propertyId === item.id }"
            @click="pickProperty(item)"
          >
            <div class="qb-card__media" :style="createMediaStyle(item.images, index)">
              <span class="qb-card__rating">
                <el-icon><StarFilled /></el-icon>{{ formatRating(item.rating) }}
              </span>
              <span v-if="item.bookingCount" class="qb-card__hot">热门 · {{ item.bookingCount }} 单</span>
            </div>
            <div class="qb-card__body">
              <div class="qb-card__title-row">
                <h3>{{ item.propertyName }}</h3>
              </div>
              <p class="qb-card__loc">
                <el-icon><LocationFilled /></el-icon>
                {{ item.city || '未知城市' }} · {{ item.district || '未知区域' }}
              </p>
              <div v-if="item.facilities?.length" class="qb-tags">
                <span v-for="f in item.facilities.slice(0, 3)" :key="f" class="qb-tag">{{ f }}</span>
                <span v-if="item.facilities.length > 3" class="qb-tag qb-tag--more">+{{ item.facilities.length - 3 }}</span>
              </div>
              <div class="qb-card__foot">
                <div class="qb-card__price">
                  <strong>{{ formatPriceFrom(item.priceRangeMin, item.priceRangeMax) }}</strong>
                  <span>/ 晚</span>
                </div>
                <el-button
                  size="small"
                  :type="form.propertyId === item.id ? 'primary' : 'default'"
                  @click.stop="pickProperty(item)"
                >
                  {{ form.propertyId === item.id ? '已选择' : '查看' }}
                </el-button>
              </div>
            </div>
          </article>
        </div>

        <!-- Empty -->
        <EmptyState
          v-else
          title="没有匹配到房源"
          description="换个城市或清除筛选条件，看看其他优质房源。"
          action-text="清除筛选"
          height="320px"
          @action="resetFilter"
        />

        <el-pagination
          v-if="!loading && total > 0"
          v-model:current-page="currentPage"
          :page-size="filters.size"
          :total="total"
          layout="prev, pager, next"
          class="qb-pagination"
          @current-change="handlePageChange"
        />
      </div>

      <!-- RIGHT: detail panel -->
      <aside ref="formCard" class="qb-detail">
        <template v-if="selectedProperty">
          <div class="qb-detail__card">
            <div class="qb-gallery">
              <div class="qb-gallery__main" :style="createMediaStyle(galleryImages[activeImage] ?? selectedProperty.images, 0)">
                <button class="qb-detail__close" title="取消选择" @click="clearSelection">
                  <el-icon><Close /></el-icon>
                </button>
              </div>
              <div v-if="galleryImages.length > 1" class="qb-gallery__thumbs">
                <button
                  v-for="(img, i) in galleryImages.slice(0, 4)"
                  :key="i"
                  class="qb-gallery__thumb"
                  :class="{ 'qb-gallery__thumb--active': activeImage === i }"
                  :style="{ backgroundImage: `url(${img})` }"
                  @click="activeImage = i"
                ></button>
              </div>
            </div>

            <div class="qb-detail__body">
              <div class="qb-detail__title">
                <h2>{{ selectedProperty.propertyName }}</h2>
                <span class="qb-detail__rating">
                  <el-icon><StarFilled /></el-icon>{{ formatRating(selectedProperty.rating) }}
                </span>
              </div>
              <p class="qb-detail__loc">
                <el-icon><LocationFilled /></el-icon>
                {{ selectedProperty.city || '未知城市' }} · {{ selectedProperty.address || '暂无地址' }}
              </p>
              <p v-if="selectedProperty.description" class="qb-detail__desc">{{ selectedProperty.description }}</p>

              <div v-if="selectedProperty.facilities?.length" class="qb-detail__section">
                <h4>设施服务</h4>
                <div class="qb-tags">
                  <span v-for="f in selectedProperty.facilities" :key="f" class="qb-tag">{{ f }}</span>
                </div>
              </div>

              <div class="qb-detail__section">
                <h4>选择房型</h4>
                <div v-if="roomTypes.length" class="qb-rooms">
                  <button
                    v-for="rt in roomTypes"
                    :key="rt.id"
                    class="qb-room"
                    :class="{ 'qb-room--active': form.roomTypeId === rt.id }"
                    @click="form.roomTypeId = rt.id"
                  >
                    <span class="qb-room__name">{{ rt.typeName }}</span>
                    <span class="qb-room__price">¥{{ Number(rt.basePrice || 0).toFixed(0) }}<small>/晚</small></span>
                  </button>
                </div>
                <p v-else class="qb-detail__hint">该房源暂无可预订房型。</p>
              </div>
            </div>

            <!-- Booking summary -->
            <div class="qb-summary">
              <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="qb-summary__form">
                <el-form-item label="入住 / 离店日期" required>
                  <el-date-picker
                    v-model="dateRange"
                    type="daterange"
                    start-placeholder="入住"
                    end-placeholder="离店"
                    style="width: 100%"
                  />
                </el-form-item>
                <div class="qb-summary__grid">
                  <el-form-item label="联系人" prop="contactName">
                    <el-input v-model="form.contactName" placeholder="姓名" />
                  </el-form-item>
                  <el-form-item label="手机号" prop="contactPhone">
                    <el-input v-model="form.contactPhone" placeholder="联系电话" />
                  </el-form-item>
                </div>
                <el-form-item label="入住人数" prop="numberOfGuests">
                  <el-input-number v-model="form.numberOfGuests" :min="1" :max="10" style="width: 100%" />
                </el-form-item>
                <el-form-item label="备注需求">
                  <el-input v-model="form.specialRequests" type="textarea" :rows="2" placeholder="特殊需求（选填）" />
                </el-form-item>

                <div v-if="estimatedTotal" class="qb-summary__total">
                  <span>预计总价 · {{ nights }} 晚</span>
                  <strong>¥{{ estimatedTotal }}</strong>
                </div>

                <el-button type="primary" size="large" class="qb-summary__submit" :loading="submitting" @click="submit">
                  确认预订
                </el-button>
                <el-alert
                  v-if="!isLoggedIn"
                  type="info"
                  title="登录后才能正式创建订单"
                  show-icon
                  :closable="false"
                  class="qb-summary__alert"
                />
              </el-form>
            </div>
          </div>
        </template>

        <!-- Default: trending + prompt -->
        <template v-else>
          <div class="qb-detail__placeholder">
            <div class="qb-placeholder__art">
              <el-icon><House /></el-icon>
            </div>
            <h3>选择一处房源查看详情</h3>
            <p>点击左侧任意房源，这里会显示图集、房型、设施和预订信息。</p>
          </div>

          <div class="qb-trending">
            <div class="qb-trending__head">
              <h4>正在热订</h4>
              <span>基于近期预订量</span>
            </div>
            <div v-if="recoList.length" class="qb-trending__list">
              <button
                v-for="(item, index) in recoList.slice(0, 4)"
                :key="item.id"
                class="qb-trending__item"
                @click="pickProperty(item)"
              >
                <span class="qb-trending__cover" :style="createMediaStyle(item.images, index)"></span>
                <span class="qb-trending__info">
                  <strong>{{ item.propertyName }}</strong>
                  <small>
                    <el-icon><StarFilled /></el-icon>{{ formatRating(item.rating) }} · {{ item.city || '未知' }}
                  </small>
                  <em>{{ formatPriceFrom(item.priceRangeMin, item.priceRangeMax) }} 起</em>
                </span>
              </button>
            </div>
            <div v-else class="qb-trending__empty">暂无热门数据</div>
          </div>
        </template>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, StarFilled, LocationFilled, Calendar, User, Close, House } from '@element-plus/icons-vue'
import EmptyState from '../components/EmptyState.vue'
import { bookingApi, propertyApi, roomTypeApi } from '../api'
import { createMediaStyle, parseImageList } from '../utils/media'

const router = useRouter()
const route = useRoute()

const properties = ref([])
const propertyOptions = ref([])
const recoList = ref([])
const roomTypes = ref([])
const loading = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const formCard = ref(null)
const dateRange = ref([])
const currentPage = ref(1)
const total = ref(0)
const selectedProperty = ref(null)
const activeImage = ref(0)

const popularCities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '三亚', '西安']

const ratingOptions = [
  { label: '4.5 分及以上', value: 4.5 },
  { label: '4.0 分及以上', value: 4.0 },
  { label: '3.5 分及以上', value: 3.5 },
  { label: '3.0 分及以上', value: 3.0 }
]

const filters = reactive({
  keyword: '',
  city: '',
  district: '',
  minRating: null,
  size: 12
})

const form = reactive({
  propertyId: null,
  roomTypeId: null,
  contactName: '',
  contactPhone: '',
  numberOfGuests: 2,
  specialRequests: ''
})

const rules = {
  contactName: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  contactPhone: [{ required: true, message: '请输入手机号', trigger: 'blur' }]
}

const isLoggedIn = computed(() => !!localStorage.getItem('user'))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / filters.size)))
const galleryImages = computed(() => parseImageList(selectedProperty.value?.images))

const nights = computed(() => {
  const [start, end] = dateRange.value || []
  if (!start || !end) return 0
  const diff = Math.round((new Date(end) - new Date(start)) / 86400000)
  return diff > 0 ? diff : 0
})

const selectedRoomPrice = computed(() => {
  const rt = roomTypes.value.find((r) => r.id === form.roomTypeId)
  return rt ? Number(rt.basePrice || 0) : 0
})

const estimatedTotal = computed(() => {
  if (!nights.value || !selectedRoomPrice.value) return ''
  return (nights.value * selectedRoomPrice.value).toFixed(0)
})

const mergePropertyOptions = (items) => {
  const source = Array.isArray(items) ? items : []
  const map = new Map()
  for (const item of propertyOptions.value) {
    if (item?.id != null) map.set(item.id, item)
  }
  for (const item of source) {
    if (item?.id != null) map.set(item.id, item)
  }
  propertyOptions.value = Array.from(map.values())
}

const formatRating = (rating) => {
  const numeric = Number(rating)
  return Number.isFinite(numeric) ? numeric.toFixed(1) : '暂无'
}

const formatPriceFrom = (min, max) => {
  const minValue = Number(min)
  const maxValue = Number(max)
  if (Number.isFinite(minValue) && minValue > 0) return `¥${minValue.toFixed(0)}`
  if (Number.isFinite(maxValue) && maxValue > 0) return `¥${maxValue.toFixed(0)}`
  return '价格待定'
}

const loadProperties = async () => {
  loading.value = true
  try {
    const params = {
      keyword: filters.keyword || undefined,
      city: filters.city || undefined,
      district: filters.district || undefined,
      minRating: filters.minRating ?? undefined,
      page: currentPage.value,
      size: filters.size
    }
    const { data } = await propertyApi.search(params)
    properties.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total || 0)
    currentPage.value = Number(data?.page || currentPage.value)
    mergePropertyOptions(properties.value)
  } catch (error) {
    properties.value = []
    total.value = 0
    ElMessage.error('加载房源失败')
  } finally {
    loading.value = false
  }
}

const loadRecommendations = async () => {
  try {
    const { data } = await propertyApi.getTop(5)
    const list = Array.isArray(data) ? data : []
    recoList.value = list
      .map((item) => {
        const property = item?.property || item
        if (!property) return null
        return { ...property, bookingCount: item?.bookingCount ?? property?.bookingCount ?? 0 }
      })
      .filter(Boolean)
    mergePropertyOptions(recoList.value)
  } catch (error) {
    recoList.value = []
  }
}

const applyFilters = () => {
  currentPage.value = 1
  loadProperties()
}

const quickCity = (city) => {
  filters.city = filters.city === city ? '' : city
  applyFilters()
}

const resetFilter = () => {
  filters.keyword = ''
  filters.city = ''
  filters.district = ''
  filters.minRating = null
  currentPage.value = 1
  loadProperties()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadProperties()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const pickProperty = (item) => {
  if (!item?.id) return
  router.push({ name: 'PropertyDetail', params: { id: item.id } })
}

const clearSelection = () => {
  form.propertyId = null
  form.roomTypeId = null
  selectedProperty.value = null
  roomTypes.value = []
}

const loadRoomTypes = async (propertyId) => {
  roomTypes.value = []
  form.roomTypeId = null
  const pid = propertyId || form.propertyId
  if (!pid) return []
  try {
    const { data } = await roomTypeApi.getActiveByPropertyId(pid)
    roomTypes.value = Array.isArray(data) ? data : []
    if (roomTypes.value.length === 1) form.roomTypeId = roomTypes.value[0].id
  } catch (error) {
    ElMessage.error('加载房型失败')
  }
  return roomTypes.value
}

const toDate = (val) => {
  if (!val) return null
  const d = new Date(val)
  return d.toISOString().split('T')[0]
}

const submit = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再提交预订')
    return
  }
  if (!form.propertyId) {
    ElMessage.warning('请先选择房源')
    return
  }
  if (!form.roomTypeId) {
    ElMessage.warning('请选择房型')
    return
  }
  await formRef.value.validate()
  if (!dateRange.value?.length) {
    ElMessage.warning('请选择入住和离店日期')
    return
  }

  submitting.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user'))
    const payload = {
      user: { id: user.id },
      property: { id: form.propertyId },
      roomType: { id: form.roomTypeId },
      checkInDate: toDate(dateRange.value[0]),
      checkOutDate: toDate(dateRange.value[1]),
      numberOfGuests: form.numberOfGuests,
      contactName: form.contactName,
      contactPhone: form.contactPhone,
      specialRequests: form.specialRequests,
      status: 'PENDING',
      paymentStatus: 'UNPAID'
    }
    const { data } = await bookingApi.create(payload)
    ElMessage.success('预订已创建，请尽快完成支付')
    formRef.value.resetFields()
    dateRange.value = []
    router.push({ name: 'Booking', query: { tab: 'cart', bookingId: data?.id } })
  } catch (error) {
    ElMessage.error(error?.response?.data?.error || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  filters.city = typeof route.query.city === 'string' ? route.query.city : ''
  filters.keyword = typeof route.query.keyword === 'string' ? route.query.keyword : ''
  loadRecommendations()
  loadProperties().then(() => {
    const pid = route.query.propertyId ? Number(route.query.propertyId) : null
    const rid = route.query.roomTypeId ? Number(route.query.roomTypeId) : null
    if (pid) {
      form.propertyId = pid
      const found = propertyOptions.value.find((p) => p.id === pid)
      if (found) selectedProperty.value = found
      loadRoomTypes(pid).then(() => {
        if (rid) form.roomTypeId = rid
      })
    }
  })
})
</script>

<style scoped>
.qb-page {
  display: grid;
  gap: 20px;
  --qb-primary: #d97757;
  --qb-card: #ffffff;
  --qb-text: #2d2926;
  --qb-radius: 22px;
}

/* ===== Hero (compact, <=260px) ===== */
.qb-hero {
  position: relative;
  max-height: 260px;
  border-radius: var(--qb-radius);
  padding: 32px 36px;
  overflow: hidden;
  background:
    linear-gradient(120deg, rgba(217, 119, 87, 0.92) 0%, rgba(168, 95, 71, 0.88) 100%),
    url('https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1600&q=60');
  background-size: cover;
  background-position: center;
  box-shadow: var(--app-shadow-md);
}

.qb-hero__inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qb-hero__eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 2px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.78);
}

.qb-hero__title {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.qb-hero__subtitle {
  margin: 0 0 14px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.88);
}

/* ===== Search bar ===== */
.qb-search {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(60, 35, 20, 0.22);
}

.qb-search__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.qb-search__field--dates {
  flex: 1.4;
}

.qb-search__field label {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-soft);
  padding-left: 4px;
}

.qb-search__field :deep(.el-input__wrapper),
.qb-search__field :deep(.el-select__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding-left: 4px;
}

.qb-search__field :deep(.el-range-editor) {
  box-shadow: none !important;
  background: transparent;
  padding: 0 4px;
}

.qb-search__sep {
  width: 1px;
  align-self: stretch;
  margin: 6px 0;
  background: var(--app-line);
}

.qb-search__btn {
  height: 48px;
  padding: 0 28px;
  border-radius: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

/* ===== Popular destination chips ===== */
.qb-chips {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.qb-chips__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-soft);
}

.qb-chips__row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.qb-chip {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid var(--app-line-strong);
  background: var(--qb-card);
  color: var(--app-text);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--app-transition);
}

.qb-chip:hover {
  border-color: var(--qb-primary);
  color: var(--qb-primary);
  transform: translateY(-1px);
}

.qb-chip--active {
  background: var(--qb-primary);
  border-color: var(--qb-primary);
  color: #fff;
}

.qb-chip--reset {
  border-style: dashed;
  color: var(--app-text-faint);
}

/* ===== Main two-column ===== */
.qb-main {
  display: grid;
  grid-template-columns: minmax(300px, 380px) 1fr;
  gap: 24px;
  align-items: start;
}

.qb-discovery {
  order: 2;
}

.qb-detail {
  order: 1;
}

.qb-discovery__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.qb-discovery__head h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--qb-text);
}

.qb-discovery__head p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--app-text-soft);
}

.qb-discovery__sort {
  width: 150px;
  flex-shrink: 0;
}

/* ===== Card grid ===== */
.qb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 18px;
}

.qb-card {
  display: flex;
  flex-direction: column;
  background: var(--qb-card);
  border-radius: var(--qb-radius);
  border: 1px solid var(--app-line);
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(60, 35, 20, 0.05);
  transition: transform var(--app-transition), box-shadow var(--app-transition), border-color var(--app-transition);
}

.qb-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 44px rgba(60, 35, 20, 0.16);
  border-color: rgba(217, 119, 87, 0.4);
}

.qb-card--active {
  border-color: var(--qb-primary);
  box-shadow: 0 16px 40px rgba(217, 119, 87, 0.24);
}

.qb-card__media {
  position: relative;
  aspect-ratio: 4 / 3;
  background-size: cover;
  background-position: center;
}

.qb-card__rating {
  position: absolute;
  top: 12px;
  left: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: #d6a45c;
  font-size: 12px;
  font-weight: 700;
}

.qb-card__hot {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(217, 119, 87, 0.92);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.qb-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px 16px;
  flex: 1;
}

.qb-card__title-row h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--qb-text);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.qb-card__loc {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  font-size: 13px;
  color: var(--app-text-soft);
}

.qb-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 4px;
}

.qb-card__price strong {
  font-size: 18px;
  font-weight: 700;
  color: var(--qb-primary);
}

.qb-card__price span {
  font-size: 12px;
  color: var(--app-text-faint);
}

/* ===== Tags ===== */
.qb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.qb-tag {
  padding: 3px 9px;
  border-radius: 8px;
  background: var(--app-surface-muted);
  color: var(--app-text-soft);
  font-size: 11px;
}

.qb-tag--more {
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
}

.qb-pagination {
  margin-top: 24px;
  justify-content: center;
}

/* ===== Detail panel (right) ===== */
.qb-detail {
  position: sticky;
  top: 94px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qb-detail__card {
  background: var(--qb-card);
  border-radius: var(--qb-radius);
  border: 1px solid var(--app-line);
  overflow: hidden;
  box-shadow: var(--app-shadow-sm);
}

/* Gallery */
.qb-gallery__main {
  position: relative;
  aspect-ratio: 16 / 10;
  background-size: cover;
  background-position: center;
}

.qb-detail__close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: var(--qb-text);
  cursor: pointer;
  transition: background var(--app-transition);
}

.qb-detail__close:hover {
  background: #fff;
}

.qb-gallery__thumbs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 8px;
}

.qb-gallery__thumb {
  aspect-ratio: 1 / 1;
  border: 2px solid transparent;
  border-radius: 10px;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  transition: border-color var(--app-transition);
}

.qb-gallery__thumb--active {
  border-color: var(--qb-primary);
}

.qb-detail__body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qb-detail__title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.qb-detail__title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--qb-text);
  line-height: 1.3;
}

.qb-detail__rating {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(214, 164, 92, 0.14);
  color: #c8881f;
  font-size: 13px;
  font-weight: 700;
}

.qb-detail__loc {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  font-size: 13px;
  color: var(--app-text-soft);
}

.qb-detail__desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-soft);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.qb-detail__section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--qb-text);
}

.qb-detail__hint {
  margin: 0;
  font-size: 13px;
  color: var(--app-text-faint);
}

/* Room types */
.qb-rooms {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qb-room {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1.5px solid var(--app-line);
  background: var(--app-bg-soft);
  cursor: pointer;
  transition: all var(--app-transition);
}

.qb-room:hover {
  border-color: rgba(217, 119, 87, 0.4);
}

.qb-room--active {
  border-color: var(--qb-primary);
  background: var(--app-primary-soft);
}

.qb-room__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--qb-text);
}

.qb-room__price {
  font-size: 16px;
  font-weight: 700;
  color: var(--qb-primary);
}

.qb-room__price small {
  font-size: 11px;
  color: var(--app-text-faint);
  font-weight: 500;
}

/* Booking summary */
.qb-summary {
  padding: 16px 20px 20px;
  border-top: 1px solid var(--app-line);
  background: var(--app-bg-soft);
}

.qb-summary__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.qb-summary__total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  margin: 4px 0 8px;
  border-top: 1px dashed var(--app-line-strong);
}

.qb-summary__total span {
  font-size: 13px;
  color: var(--app-text-soft);
}

.qb-summary__total strong {
  font-size: 22px;
  font-weight: 700;
  color: var(--qb-primary);
}

.qb-summary__submit {
  width: 100%;
}

.qb-summary__alert {
  margin-top: 12px;
}

/* ===== Default placeholder + trending ===== */
.qb-detail__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  padding: 32px 24px;
  background: var(--qb-card);
  border-radius: var(--qb-radius);
  border: 1px dashed var(--app-line-strong);
}

.qb-placeholder__art {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--app-primary-soft);
  color: var(--qb-primary);
  font-size: 28px;
  margin-bottom: 4px;
}

.qb-detail__placeholder h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--qb-text);
}

.qb-detail__placeholder p {
  margin: 0;
  font-size: 13px;
  color: var(--app-text-soft);
  line-height: 1.6;
}

.qb-trending {
  background: var(--qb-card);
  border-radius: var(--qb-radius);
  border: 1px solid var(--app-line);
  padding: 16px 18px;
  box-shadow: var(--app-shadow-sm);
}

.qb-trending__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}

.qb-trending__head h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--qb-text);
}

.qb-trending__head span {
  font-size: 12px;
  color: var(--app-text-faint);
}

.qb-trending__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.qb-trending__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid transparent;
  background: var(--app-bg-soft);
  cursor: pointer;
  text-align: left;
  transition: all var(--app-transition);
}

.qb-trending__item:hover {
  border-color: rgba(217, 119, 87, 0.4);
  transform: translateX(2px);
}

.qb-trending__cover {
  width: 64px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 10px;
  background-size: cover;
  background-position: center;
}

.qb-trending__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.qb-trending__info strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--qb-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qb-trending__info small {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--app-text-faint);
}

.qb-trending__info em {
  font-style: normal;
  font-size: 13px;
  font-weight: 700;
  color: var(--qb-primary);
}

.qb-trending__empty {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--app-text-faint);
}

/* ===== Skeleton ===== */
.qb-card--skeleton {
  cursor: default;
}

.qb-card--skeleton:hover {
  transform: none;
  box-shadow: 0 6px 18px rgba(60, 35, 20, 0.05);
  border-color: var(--app-line);
}

.sk-line {
  height: 13px;
  border-radius: 999px;
  margin-bottom: 8px;
}

.sk-line--lg {
  width: 75%;
  height: 16px;
}

.sk-line--sm {
  width: 45%;
}

/* ===== Responsive ===== */
@media (max-width: 1100px) {
  .qb-main {
    grid-template-columns: 1fr;
  }

  .qb-detail {
    position: static;
  }
}

@media (max-width: 768px) {
  .qb-hero {
    max-height: none;
    padding: 24px 20px;
  }

  .qb-hero__title {
    font-size: 24px;
  }

  .qb-search {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .qb-search__sep {
    display: none;
  }

  .qb-search__field :deep(.el-input__wrapper),
  .qb-search__field :deep(.el-select__wrapper),
  .qb-search__field :deep(.el-range-editor) {
    box-shadow: 0 0 0 1px var(--app-line) inset !important;
    padding: 4px 11px;
  }

  .qb-search__btn {
    width: 100%;
  }

  .qb-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }

  .qb-discovery__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .qb-summary__grid {
    grid-template-columns: 1fr;
  }
}










</style>


