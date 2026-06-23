<template>
  <div class="property-detail">
    <!-- Back Navigation -->
    <div class="detail-nav">
      <button class="back-link" @click="$router.back()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        <span>Back</span>
      </button>
      <span class="nav-title">{{ property.propertyName || 'Property Detail' }}</span>
    </div>

    <!-- Loading Skeleton -->
    <el-skeleton :loading="loading" animated>
      <template #template>
        <div class="skeleton-layout">
          <div class="soft-skeleton skeleton-gallery"></div>
          <div class="soft-skeleton skeleton-summary"></div>
        </div>
      </template>

      <template #default>
        <!-- ═══════════════════════════════════════════ -->
        <!-- FIRST SCREEN: Gallery + Summary             -->
        <!-- ═══════════════════════════════════════════ -->
        <section class="hero-section fade-rise">
          <div class="hero-gallery">
            <HotelGallery :images="galleryImages" />
          </div>
          <div class="hero-summary">
            <HotelSummary
              :property="property"
              :review-count="reviewCount"
              @book="openBooking()"
              @favorite="onFavorite"
              @share="onShare"
            />
          </div>
        </section>

        <!-- ═══════════════════════════════════════════ -->
        <!-- ROOM TYPES SECTION                          -->
        <!-- ═══════════════════════════════════════════ -->
        <section id="rooms" ref="roomsSectionRef" class="rooms-section fade-rise">
          <div class="section-header">
            <div>
              <p class="section-kicker">Room Types</p>
              <h2 class="section-title">Choose your perfect stay</h2>
            </div>
            <span v-if="roomTypes.length" class="section-count">{{ roomTypes.length }} room{{ roomTypes.length > 1 ? 's' : '' }}</span>
          </div>

          <div v-if="roomTypes.length" class="rooms-grid">
            <RoomCard
              v-for="(rt, idx) in roomTypes"
              :key="rt.id || idx"
              :room-type="rt"
              :index="idx"
              @book="openBooking($event)"
            />
          </div>
          <EmptyState
            v-else
            title="No room types available"
            description="Rooms will appear here once they've been added."
          />
        </section>

        <!-- ═══════════════════════════════════════════ -->
        <!-- INFO TABS SECTION                          -->
        <!-- ═══════════════════════════════════════════ -->
        <section class="info-section fade-rise">
          <HotelTabs
            :property="property"
            :facilities="facilities"
            :policies="policies"
            :review-count="reviewCount"
          />
        </section>
      </template>
    </el-skeleton>

    <!-- ═══════════════════════════════════════════ -->
    <!-- BOOKING DIALOG (unchanged logic)            -->
    <!-- ═══════════════════════════════════════════ -->
    <el-dialog v-model="bookingDialog" title="Quick Booking" width="560px" class="booking-dialog">
      <el-form :model="bookingForm" label-position="top" ref="bookingFormRef" :rules="bookingRules">
        <el-form-item label="Room Type" prop="roomTypeId">
          <el-select v-model="bookingForm.roomTypeId" placeholder="Select a room type" style="width: 100%">
            <el-option
              v-for="(rt, idx) in roomTypes"
              :key="rt.id || idx"
              :label="`${rt.typeName} · ¥${Number(rt.basePrice || 0).toFixed(2)}`"
              :value="rt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Check-in / Check-out" prop="dates">
          <el-date-picker
            v-model="bookingForm.dates"
            type="daterange"
            start-placeholder="Check-in"
            end-placeholder="Check-out"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="Guests" prop="guests">
          <el-input-number v-model="bookingForm.guests" :min="1" :max="6" />
        </el-form-item>
        <el-form-item label="Price Preview">
          <div class="price-preview">
            <div>Per night: ¥{{ currentPrice.toFixed(2) }}</div>
            <div>Stay: {{ nights }} night{{ nights > 1 ? 's' : '' }}</div>
            <div class="price-preview__total">Estimated total: ¥{{ estimatedTotal }}</div>
          </div>
        </el-form-item>
        <el-form-item label="Contact Name" prop="contactName">
          <el-input v-model="bookingForm.contactName" placeholder="Your name" />
        </el-form-item>
        <el-form-item label="Contact Phone" prop="contactPhone">
          <el-input v-model="bookingForm.contactPhone" placeholder="Your phone number" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bookingDialog = false">Cancel</el-button>
        <el-button type="primary" @click="submitBooking" :loading="submitting">Confirm Booking</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import EmptyState from '../components/EmptyState.vue'
import HotelGallery from '../components/hotel/HotelGallery.vue'
import HotelSummary from '../components/hotel/HotelSummary.vue'
import HotelTabs from '../components/hotel/HotelTabs.vue'
import RoomCard from '../components/hotel/RoomCard.vue'
import { propertyApi, bookingApi } from '../api'

// ── Router ────────────────────────────────────────
const route = useRoute()
const router = useRouter()

// ── State ─────────────────────────────────────────
const property = ref({})
const roomTypes = ref([])
const loading = ref(false)
const bookingDialog = ref(false)
const submitting = ref(false)
const bookingFormRef = ref(null)
const roomsSectionRef = ref(null)
const bookingForm = ref({
  roomTypeId: null,
  dates: [],
  guests: 2,
  contactName: '',
  contactPhone: ''
})

// ── Static Fallbacks ──────────────────────────────
const STATIC_IMAGES = [
  'https://pic.nximg.cn/20120414/128199_105320827000_2.jpg',
  'https://pic.nximg.cn/file/20200603/128199_102610317000_2.jpg'
]
const STATIC_FACILITIES = [
  'Free high-speed Wi-Fi throughout',
  '24-hour front desk & self check-in',
  'Air conditioning / underfloor heating',
  'Breakfast available (advance booking required)',
  'Free luggage storage & taxi assistance',
  'Washer / dryer (selected rooms)',
  'Disposable toiletries & hair dryer provided'
]
const STATIC_POLICIES = [
  'Check-in after 14:00, check-out before 12:00. Early check-in or late check-out by arrangement; fees may apply.',
  'Free cancellation 24+ hours before check-in. Cancellations within 24 hours are subject to platform policy.',
  'A deposit may be required for select room types; refundable after inspection.',
  'Strictly non-smoking indoors. Deep-cleaning fees apply for violations.',
  'Pets are not accommodated at this time.',
  'Children under 12 stay free with parents (excludes extra bed and breakfast).',
  'Accommodation invoices available — please provide billing details before check-out.'
]

// ── Review count (placeholder) ────────────────────
const reviewCount = ref(126)

// ── Parsing Helpers ───────────────────────────────
const parseList = (val) => {
  if (!val) return []
  if (Array.isArray(val)) return val.filter(x => typeof x === 'string' && x.trim())
  try {
    const parsed = JSON.parse(val)
    return Array.isArray(parsed) ? parsed.filter(x => typeof x === 'string' && x.trim()) : []
  } catch {
    if (typeof val === 'string') {
      return val.split(/[,\n，、;]/).map(x => x.trim()).filter(Boolean)
    }
    return []
  }
}

const facilities = computed(() => {
  const db = parseList(property.value.facilities)
  return db.length ? db : STATIC_FACILITIES
})

const policies = computed(() => {
  const db = parseList(property.value.policies)
  return db.length ? db : STATIC_POLICIES
})

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

const galleryImages = computed(() => {
  const db = parseImages(property.value.images)
  return db.length ? db : STATIC_IMAGES
})

// ── Data Loading ──────────────────────────────────
const loadDetail = async () => {
  loading.value = true
  try {
    const { data } = await propertyApi.getDetail(route.params.id)
    property.value = data.property || {}
    roomTypes.value = data.roomTypes || []
    if (route.hash === '#rooms') {
      await nextTick()
      roomsSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  } catch {
    ElMessage.error('Failed to load property details')
  } finally {
    loading.value = false
  }
}

// ── Booking Logic (unchanged) ─────────────────────
const goBook = (roomType) => {
  router.push({
    name: 'SimpleBooking',
    query: {
      propertyId: property.value.id,
      roomTypeId: roomType?.id
    }
  })
}

const openBooking = (rt) => {
  bookingDialog.value = true
  bookingForm.value = {
    roomTypeId: rt?.id || roomTypes.value[0]?.id || null,
    dates: [],
    guests: 2,
    contactName: '',
    contactPhone: ''
  }
}

const bookingRules = {
  roomTypeId: [{ required: true, message: 'Please select a room type', trigger: 'change' }],
  dates: [{ type: 'array', required: true, message: 'Please select check-in and check-out dates', trigger: 'change' }],
  contactName: [{ required: true, message: 'Please enter contact name', trigger: 'blur' }],
  contactPhone: [{ required: true, message: 'Please enter contact phone', trigger: 'blur' }]
}

const nights = computed(() => {
  if (!bookingForm.value.dates?.length) return 1
  const [start, end] = bookingForm.value.dates
  if (!start || !end) return 1
  const diff = Math.round((new Date(end) - new Date(start)) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 1
})

const currentPrice = computed(() => {
  const rt = roomTypes.value.find(item => item.id === bookingForm.value.roomTypeId)
  return Number(rt?.basePrice || 0)
})

const estimatedTotal = computed(() => (currentPrice.value * nights.value || 0).toFixed(2))

const submitBooking = async () => {
  try {
    await bookingFormRef.value.validate()
    submitting.value = true
    const [checkIn, checkOut] = bookingForm.value.dates || []
    const payload = {
      user: { id: JSON.parse(localStorage.getItem('user') || '{}').id },
      property: { id: property.value.id },
      roomType: { id: bookingForm.value.roomTypeId },
      checkInDate: toDate(checkIn),
      checkOutDate: toDate(checkOut),
      numberOfGuests: bookingForm.value.guests,
      contactName: bookingForm.value.contactName,
      contactPhone: bookingForm.value.contactPhone,
      status: 'PENDING',
      paymentStatus: 'UNPAID'
    }
    const { data } = await bookingApi.create(payload)
    ElMessage.success('Booking created! Please complete payment.')
    bookingDialog.value = false
    router.push({
      name: 'Booking',
      query: { tab: 'cart', bookingId: data?.id }
    })
  } catch (error) {
    if (error !== false) {
      ElMessage.error(error?.response?.data?.error || 'Booking failed')
    }
  } finally {
    submitting.value = false
  }
}

const toDate = (val) => {
  if (!val) return null
  return new Date(val).toISOString().split('T')[0]
}

// ── User Actions ──────────────────────────────────
const onFavorite = () => {
  ElMessage.success('Added to favorites!')
}

const onShare = () => {
  const url = window.location.href
  navigator.clipboard?.writeText(url)
    .then(() => ElMessage.success('Link copied to clipboard!'))
    .catch(() => ElMessage.info('Share this page: ' + url))
}

// ── Init ──────────────────────────────────────────
onMounted(loadDetail)
</script>

<style scoped>
/* ═══════════════════════════════════════════════ */
/* PAGE CONTAINER                                  */
/* ═══════════════════════════════════════════════ */
.property-detail {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px 60px;
  display: flex;
  flex-direction: column;
  gap: 36px;
}

/* ── Back Navigation ── */
.detail-nav {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid rgba(128, 93, 72, 0.12);
  background: rgba(255, 255, 255, 0.65);
  color: #5c4a3a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.back-link:hover {
  background: #fff;
  border-color: rgba(201, 134, 106, 0.3);
  color: #c97a50;
}

.nav-title {
  font-size: 14px;
  color: #aa9890;
  font-weight: 500;
}

/* ═══════════════════════════════════════════════ */
/* HERO SECTION: Gallery + Summary                 */
/* ═══════════════════════════════════════════════ */
.hero-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
  align-items: start;
}

.hero-gallery {
  position: sticky;
  top: 20px;
}

.hero-summary {
  display: flex;
  flex-direction: column;
}

/* ═══════════════════════════════════════════════ */
/* ROOM TYPES SECTION                              */
/* ═══════════════════════════════════════════════ */
.rooms-section {
  padding: 36px;
  border-radius: 28px;
  background: rgba(255, 253, 249, 0.78);
  border: 1px solid rgba(128, 93, 72, 0.08);
  box-shadow: 0 12px 36px rgba(114, 83, 60, 0.05);
  backdrop-filter: blur(12px);
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 12px;
}

.section-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #c97a50;
}

.section-title {
  margin: 0;
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 700;
  color: #3f312c;
  line-height: 1.2;
}

.section-count {
  padding: 6px 16px;
  border-radius: 999px;
  background: rgba(246, 237, 229, 0.7);
  color: #7d6d66;
  font-size: 13px;
  font-weight: 600;
}

.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

/* ═══════════════════════════════════════════════ */
/* INFO TABS SECTION                               */
/* ═══════════════════════════════════════════════ */
.info-section {
  padding: 36px;
  border-radius: 28px;
  background: rgba(255, 253, 249, 0.78);
  border: 1px solid rgba(128, 93, 72, 0.08);
  box-shadow: 0 12px 36px rgba(114, 83, 60, 0.05);
  backdrop-filter: blur(12px);
}

/* ═══════════════════════════════════════════════ */
/* SKELETON                                        */
/* ═══════════════════════════════════════════════ */
.skeleton-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
}

.skeleton-gallery {
  aspect-ratio: 4 / 3;
  border-radius: 24px;
}

.skeleton-summary {
  min-height: 480px;
  border-radius: 24px;
}

/* ═══════════════════════════════════════════════ */
/* BOOKING DIALOG OVERRIDES                        */
/* ═══════════════════════════════════════════════ */
.price-preview {
  display: grid;
  gap: 6px;
  padding: 14px 18px;
  border-radius: 16px;
  background: rgba(255, 248, 241, 0.8);
  color: #7d6d66;
  font-size: 14px;
}

.price-preview__total {
  color: #c97a50;
  font-weight: 700;
  font-size: 16px;
}

/* ═══════════════════════════════════════════════ */
/* RESPONSIVE                                      */
/* ═══════════════════════════════════════════════ */
@media (max-width: 1024px) {
  .hero-section {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .hero-gallery {
    position: static;
  }

  .rooms-grid {
    grid-template-columns: 1fr;
  }

  .skeleton-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .property-detail {
    padding: 14px 16px 40px;
    gap: 24px;
  }

  .rooms-section,
  .info-section {
    padding: 24px 20px;
    border-radius: 22px;
  }

  .rooms-grid {
    grid-template-columns: 1fr;
  }
}
</style>
