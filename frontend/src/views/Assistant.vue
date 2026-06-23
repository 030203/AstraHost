<template>
  <div class="concierge">
    <aside v-if="!isPreviewMode" class="side" :class="{ 'side--hidden': !sidebarOpen }">
      <div class="side__inner">
        <button class="brand" type="button" title="返回首页" @click="router.push('/')">
          <div class="brand__mark">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 2.5l2.7 6.3 6.8.5-5.2 4.4 1.7 6.6L12 16.9 5.9 20.8l1.7-6.6L2.4 9.8l6.8-.5L12 2.5z" fill="currentColor" />
            </svg>
          </div>
          <div class="brand__copy">
            <strong>AstraHost</strong>
            <span>AI Concierge</span>
          </div>
        </button>

        <button class="new-chat" type="button" @click="resetConversation">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          <span>开启新对话</span>
        </button>

        <div v-if="favoriteConversations.length" class="side__group">
          <p class="side__label">收藏</p>
          <ul class="conv-list">
            <li v-for="item in favoriteConversations" :key="item.id">
              <button
                class="conv"
                :class="{ 'conv--active': item.id === conversationId }"
                type="button"
                @click="activateConversation(item.id)"
              >
                <span class="conv__star">★</span>
                <span class="conv__title">{{ item.title }}</span>
              </button>
            </li>
          </ul>
        </div>

        <div class="side__group side__group--grow">
          <p class="side__label">历史对话</p>
          <ul v-if="recentConversations.length" class="conv-list">
            <li v-for="item in recentConversations" :key="item.id">
              <button
                class="conv"
                :class="{ 'conv--active': item.id === conversationId }"
                type="button"
                @click="activateConversation(item.id)"
              >
                <span class="conv__title">{{ item.title }}</span>
                <span class="conv__actions">
                  <span
                    class="conv__icon"
                    :class="{ 'conv__icon--on': isFavorite(item.id) }"
                    title="收藏"
                    @click.stop="toggleFavorite(item.id)"
                  >★</span>
                  <span class="conv__icon" title="删除" @click.stop="deleteConversation(item.id)">
                    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M5 7h14M10 7V5h4v2M6 7l1 13h10l1-13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </span>
                </span>
              </button>
            </li>
          </ul>
          <p v-else class="side__empty">还没有对话，开始问我酒店推荐吧。</p>
        </div>

        <div class="user">
          <div class="user__avatar">{{ userInitial }}</div>
          <div class="user__copy">
            <strong>{{ userContext?.username || '贵宾住客' }}</strong>
            <span>{{ roleText(userContext?.role) }}</span>
          </div>
          <button class="user__cog" type="button" title="个人设置" @click="router.push('/profile')">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M9 5l1-2h4l1 2 2 1 2-1 2 3-1 2v2l1 2-2 3-2-1-2 1-1 2h-4l-1-2-2-1-2 1-2-3 1-2v-2l-1-2 2-3 2 1 2-1z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" />
              <circle cx="12" cy="12" r="2.4" stroke="currentColor" stroke-width="1.3" />
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <button class="topbar__menu" type="button" aria-label="切换侧栏" @click="sidebarOpen = !sidebarOpen">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          </svg>
        </button>
        <div class="topbar__title">
          <h1><span class="topbar__spark">✦</span> Astra AI Concierge</h1>
          <p>酒店推荐、出行灵感与一键承接</p>
        </div>
        <div v-if="isPreviewMode" class="topbar__preview-pill">酒店卡片预览</div>
        <div v-else class="topbar__spacer"></div>
      </header>

      <div ref="scrollRef" class="stage" :class="{ 'stage--welcome': isWelcome }">
        <section v-if="isWelcome" class="welcome">
          <div class="welcome__halo"></div>
          <div class="welcome__orb">✦</div>
          <h2 class="welcome__title">说出预算、城市和偏好</h2>
          <p class="welcome__sub">我会直接给你可点击的酒店卡片，不再让你看一大段纯文本清单。</p>

          <div class="chips">
            <button
              v-for="chip in welcomeChips"
              :key="chip"
              class="chip"
              type="button"
              @click="quickSend(chip)"
            >
              {{ chip }}
            </button>
          </div>
        </section>

        <div v-else class="thread">
          <template v-for="item in messages" :key="item.id">
            <article v-if="item.role === 'user'" class="row row--user">
              <div class="bubble bubble--user">{{ item.content }}</div>
            </article>

            <article v-else class="row row--ai">
              <div class="ai-avatar">✦</div>
              <div class="bubble bubble--ai" :class="{ 'bubble--error': item.error }">
                <div
                  v-if="getRenderableContent(item)"
                  class="prose"
                  :class="{ 'prose--summary': hasHotelCards(item) }"
                  v-html="renderMarkdown(getRenderableContent(item))"
                />
                <div v-else-if="loading && item.id === streamingId" class="dots">
                  <span></span><span></span><span></span>
                </div>

                <section v-if="getHotelCategories(item)?.length" class="recos">
                  <div class="recos__head">
                    <div>
                      <h3 class="recos__title">酒店推荐</h3>
                      <p v-if="getHotelSubtitle(item)" class="recos__sub">{{ getHotelSubtitle(item) }}</p>
                    </div>
                  </div>
                  <HotelCardGrid :categories="getHotelCategories(item)" />
                </section>

                <div v-if="item.pendingAction" class="pending">
                  <div class="pending__copy">
                    <strong>需要您确认</strong>
                    <p v-if="item.pendingAction.summary?.target_label">
                      {{ item.pendingAction.summary.target_label }}
                    </p>
                    <p v-if="item.pendingAction.summary?.impact" class="pending__impact">
                      {{ item.pendingAction.summary.impact }}
                    </p>
                  </div>
                  <button class="pending__btn" type="button" @click="confirmPendingAction(item.pendingAction)">
                    确认执行
                  </button>
                </div>
              </div>
            </article>
          </template>
        </div>
      </div>

      <div class="composer">
        <div class="composer__glass">
          <button class="composer__icon" type="button" title="附件">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 12.5l-8.5 8.5a5 5 0 01-7-7L13 6a3.5 3.5 0 015 5l-8.5 8.5a2 2 0 01-3-3l8-8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <button class="composer__icon" type="button" title="图片">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="3.5" y="5" width="17" height="14" rx="2.5" stroke="currentColor" stroke-width="1.6" />
              <circle cx="8.5" cy="10" r="1.6" stroke="currentColor" stroke-width="1.4" />
              <path d="M5 17l4.5-4 3 2.5L16 12l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>

          <textarea
            ref="inputRef"
            v-model="draft"
            class="composer__input"
            rows="1"
            :disabled="loading"
            placeholder="例如：广州，预算1000以内，想要机场附近、高评分酒店"
            @input="autoGrow"
            @keydown.enter.exact.prevent="sendMessage()"
          />

          <button class="composer__icon composer__icon--voice" type="button" title="语音">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="9" y="3" width="6" height="11" rx="3" stroke="currentColor" stroke-width="1.6" />
              <path d="M5.5 11a6.5 6.5 0 0013 0M12 17.5V21" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </button>

          <button class="composer__send" :disabled="loading || !draft.trim()" type="button" @click="sendMessage()">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M5 12l14-7-5 14-2.5-5.5L5 12z" fill="currentColor" />
            </svg>
          </button>
        </div>
        <p v-if="errorText" class="composer__err">{{ errorText }}</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { propertyApi } from '../api'
import {
  getAssistantConversationIds,
  getAssistantConversationMessages,
  readAssistantUserContext,
  streamAssistantChat
} from '../api/assistant'
import HotelCardGrid from '../components/hotel/HotelCardGrid.vue'
import { useAssistantConversations } from '../composables/useAssistantConversations'
import { parseHotelRecommendations, inferCityFromText } from '../utils/hotelParser'
import { parseImageList } from '../utils/media'

const router = useRouter()
const route = useRoute()
const scrollRef = ref(null)
const inputRef = ref(null)
const draft = ref('')
const loading = ref(false)
const errorText = ref('')
const conversationId = ref('')
const messages = ref([])
const streamingId = ref('')
const userContext = ref(readAssistantUserContext())
const pendingAction = ref(null)
const abortController = ref(null)
const sidebarOpen = ref(true)

const FAV_KEY = 'astra-concierge-favorites'
const HOTEL_CARD_HYDRATION_VERSION = 3
const PROPERTY_BASE_URL = 'http://localhost:5400'
const FALLBACK_CARD_IMAGE =
  'data:image/svg+xml;charset=UTF-8,' +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#F6EEE7"/>
          <stop offset="100%" stop-color="#E2C6B3"/>
        </linearGradient>
      </defs>
      <rect width="640" height="480" fill="url(#g)"/>
      <g fill="none" stroke="#B8744D" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" opacity="0.72">
        <path d="M116 334l96-102 86 80 114-126 112 152"/>
        <circle cx="224" cy="160" r="24"/>
      </g>
    </svg>
  `)

const favorites = ref(readFavorites())
const propertySearchCache = new Map()
const cityPropertyCache = new Map()

const { items: conversations, save, remove, syncRemote, getById } = useAssistantConversations()

const welcomeChips = [
  '帮我找三亚海景酒店',
  '预算1000元推荐酒店',
  '适合情侣度假的酒店',
  '帮我规划周末旅行'
]

const demoAssistantAnswer = `以下是为您推荐的广东地区预算1000元以内的精选酒店，按评分高低排列：

1. 尚品假日酒店（广州白云机场店）
📍 广州·白云区
💰 价格区间：约280~380元/晚
⭐ 评分：4.8
✨ 特色：免费接送机、停车场、茶室，性价比超高

2. 深圳罗湖万象城Aoki轻奢公寓
📍 深圳·罗湖
💰 价格区间：约280~380元/晚
⭐ 评分：4.8
✨ 特色：近万象城、地铁口、设计感强，适合短住

3. 远怡酒店（深圳宝安机场店）
📍 深圳·宝安
💰 价格区间：约300~420元/晚
⭐ 评分：4.7
✨ 特色：机场通勤方便，适合转机和商务出差`

const userInitial = computed(() => getInitial(userContext.value?.username || 'A'))
const isPreviewMode = computed(() => route.path === '/assistant-preview' || route.query.demo === 'hotels')
const isWelcome = computed(() => !loading.value && messages.value.length === 0)
const recentConversations = computed(() => {
  if (isPreviewMode.value) return []
  return conversations.value.filter((item) => !favorites.value.includes(item.id))
})
const favoriteConversations = computed(() => {
  if (isPreviewMode.value) return []
  return conversations.value.filter((item) => favorites.value.includes(item.id))
})

function readFavorites() {
  try {
    const raw = localStorage.getItem(FAV_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const isFavorite = (id) => favorites.value.includes(id)

const toggleFavorite = (id) => {
  favorites.value = favorites.value.includes(id)
    ? favorites.value.filter((item) => item !== id)
    : [...favorites.value, id]
  localStorage.setItem(FAV_KEY, JSON.stringify(favorites.value))
}

const roleText = (role) => ({ USER: '住客', MERCHANT: '商户', ADMIN: '管理员' }[role] || '会员')

const getInitial = (value) => {
  const text = String(value || '').trim()
  return text ? text.slice(0, 1).toUpperCase() : 'A'
}

const renderMarkdown = (text) => {
  if (!text) return ''
  const escaped = String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  let html = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
  html = html.replace(/\n/g, '<br>')
  return html
}

const CHINESE_VARIANT_MAP = new Map([
  ['爾', '尔'],
  ['頓', '顿'],
  ['歡', '欢'],
  ['華', '华'],
  ['強', '强'],
  ['萬', '万'],
  ['羅', '罗'],
  ['灣', '湾'],
  ['亞', '亚'],
  ['龍', '龙'],
  ['崗', '岗'],
  ['寶', '宝'],
  ['國', '国'],
  ['際', '际'],
  ['機', '机'],
  ['場', '场'],
  ['樓', '楼'],
  ['飯', '饭'],
  ['門', '门'],
  ['東', '东'],
  ['廣', '广'],
  ['區', '区'],
  ['號', '号'],
  ['悅', '悦'],
  ['麗', '丽'],
  ['賓', '宾'],
  ['閣', '阁'],
  ['軒', '轩'],
  ['匯', '汇'],
  ['總', '总'],
  ['會', '会'],
  ['濱', '滨'],
  ['島', '岛'],
  ['凱', '凯'],
  ['蘭', '兰']
])

const normalizeChineseVariants = (value) =>
  String(value || '')
    .split('')
    .map((char) => CHINESE_VARIANT_MAP.get(char) || char)
    .join('')

const normalizeTextKey = (value) =>
  normalizeChineseVariants(value)
    .toLowerCase()
    .replace(/[（）。、，,\-—_·・:：'"“”‘’|｜/\\\s]/g, '')
    .trim()

const stripBracketText = (value) =>
  String(value || '').replace(/[（(][^()（）]{0,40}[)）]/g, ' ')

const simplifyHotelName = (value) =>
  String(value || '')
    .replace(/酒店|公寓|民宿|客栈|旅馆|度假村|hotel|resort|apartment|inn/gi, '')
    .trim()

const buildHotelNameVariants = (value) =>
  [
    value,
    stripBracketText(value),
    simplifyHotelName(value),
    simplifyHotelName(stripBracketText(value))
  ]
    .map((item) => normalizeTextKey(item))
    .filter(Boolean)
    .filter((item, index, list) => list.indexOf(item) === index)

const GENERIC_TAGS = new Set(['设施', '服务', '配套', '项目', '详情', '酒店', '房源', '推荐'])

const cleanInlineText = (value) =>
  String(value || '')
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/\s+/g, ' ')
    .trim()

const compactCategoryName = (value, fallback = '精选推荐') => {
  const text = cleanInlineText(value)
    .replace(/\s*·\s*(?:房源|酒店)推荐$/i, '')
    .replace(/(?:房源|酒店)推荐$/i, '')
    .replace(/推荐$/i, '')
    .trim()
  return text || fallback
}

const sanitizeHotelName = (value) =>
  cleanInlineText(value)
    .replace(/^[🏖️🏨🥇🥈🥉⭐✨🔥\s]+/u, '')
    .replace(/^(?:TOP\s*\d+\s*[:：-]?\s*|\d+\s*[.)、:：-]\s*|第\s*\d+\s*名\s*[:：-]?\s*)/i, '')
    .replace(/^\|\s*/, '')
    .replace(/\s*\|$/, '')
    .trim()

const sanitizeLocationLabel = (value) =>
  cleanInlineText(value)
    .replace(/^(?:位置|地址|地区|位于|靠近|商圈)\s*[:：·-]?\s*/i, '')
    .replace(/[|｜]+/g, ' ')
    .trim()

const sanitizeHighlightText = (value) =>
  cleanInlineText(value)
    .replace(/^(?:亮点|特色|推荐理由|适合人群|项目|详情)\s*[:：·-]?\s*/i, '')
    .replace(/^\|\s*/, '')
    .replace(/\s*\|$/, '')
    .trim()

const isPlaceholderLocation = (value) => {
  const text = cleanInlineText(value)
  return ['位置待确认', '暂未提供', '未知', '无法确认', '暂无'].includes(text)
}

const isUsableActionUrl = (value) => {
  const text = String(value || '').trim()
  if (!text) return false
  if (text === '#') return false
  if (/^javascript:/i.test(text)) return false
  return true
}

const sanitizeChipList = (list, limit = 4) => {
  const raw = Array.isArray(list) ? list : [list]
  const items = raw
    .flatMap((item) => String(item || '').split(/[、，,\/|｜]/))
    .map((item) => sanitizeHighlightText(item))
    .filter(Boolean)
    .filter((item) => !GENERIC_TAGS.has(item))
  return items.filter((item, index) => items.indexOf(item) === index).slice(0, limit)
}

const normalizeImageUrl = (value) => {
  if (!value || typeof value !== 'string') return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  if (/^(https?:\/\/|data:image\/)/i.test(trimmed)) return trimmed
  if (trimmed.startsWith('/')) return `${PROPERTY_BASE_URL}${trimmed}`
  if (/^(uploads|static)\//i.test(trimmed)) return `${PROPERTY_BASE_URL}/${trimmed.replace(/^\/+/, '')}`
  return ''
}

const safeImage = (value) => {
  return normalizeImageUrl(value) || FALLBACK_CARD_IMAGE
}

const parseLocalPath = (url) => {
  if (!url || typeof url !== 'string') return ''
  const trimmed = url.trim()
  if (!trimmed) return ''
  if (trimmed.startsWith('/')) return trimmed
  const localMatch = trimmed.match(/^https?:\/\/localhost(?::\d+)?(\/[^?#]*(?:[?#].*)?)$/i)
  return localMatch ? localMatch[1] : ''
}

const normalizePropertyId = (value) => {
  const text = String(value ?? '').trim()
  return /^\d+$/.test(text) ? text : ''
}

const extractPropertyIdFromUrl = (url) => {
  const source = parseLocalPath(url) || String(url || '').trim()
  if (!source) return ''

  const pathMatch = source.match(/\/property\/(\d+)(?:[/?#]|$)/)
  if (pathMatch) return pathMatch[1]

  try {
    const normalized = source.startsWith('http')
      ? new URL(source)
      : new URL(source, PROPERTY_BASE_URL)
    return normalizePropertyId(normalized.searchParams.get('propertyId'))
  } catch {
    return ''
  }
}

const AREA_LABELS = [
  { label: '亚龙湾', tokens: ['亚龙湾', 'yalong bay', 'yalongwan'] },
  { label: '大东海', tokens: ['大东海', 'dadonghai'] },
  { label: '海棠湾', tokens: ['海棠湾', 'haitang bay'] },
  { label: '三亚湾', tokens: ['三亚湾', 'sanya bay'] },
  { label: '凤凰机场', tokens: ['凤凰机场', 'phoenix airport', 'sanya phoenix international airport'] },
  { label: '鹿回头', tokens: ['鹿回头', 'luhuitou'] },
  { label: '市区', tokens: ['市区', 'downtown'] }
]

const DISTRICT_LABELS = [
  { label: '吉阳区', tokens: ['jiyang district', 'jiyang'] },
  { label: '天涯区', tokens: ['tianya district', 'tianya'] },
  { label: '海棠区', tokens: ['haitang district', 'haitang'] },
  { label: '崖州区', tokens: ['yazhou district', 'yazhou'] },
  { label: '崖城', tokens: ['yacheng'] },
  { label: '福田区', tokens: ['futian district', 'futian', 'huaqiangbei'] },
  { label: '南山区', tokens: ['nanshan district', 'nanshan', 'qianhai', 'shekou'] },
  { label: '罗湖区', tokens: ['luohu district', 'luohu', 'dongmen', 'lo wu'] },
  { label: '宝安区', tokens: ['baoan district', "bao'an district", 'baoan', "bao'an", 'airport t3', 'hourui'] },
  { label: '龙华区', tokens: ['longhua district', 'longhua'] },
  { label: '盐田区', tokens: ['yantian district', 'yantian'] },
  { label: '大鹏新区', tokens: ['dapeng new district', 'dapeng'] }
]

const FACILITY_LABELS = new Map([
  ['Spa', 'Spa'],
  ['Massage room', '按摩房'],
  ['Executive lounge', '行政酒廊'],
  ['Private parking', '私家停车'],
  ['Public parking', '公共停车'],
  ['EV charging station', '充电桩'],
  ['Water park', '水上乐园'],
  ['Playground', '儿童乐园'],
  ['Sunbathing area', '日光露台'],
  ['Billiards room', '台球室'],
  ['Cardroom', '棋牌室'],
  ['Multi-function room', '多功能厅'],
  ['Secretarial services', '秘书服务'],
  ['Station pick-up', '接站服务'],
  ['Airport pick-up service', '接机服务'],
  ['Airport shuttle', '机场接驳'],
  ['Car rentals', '租车服务'],
  ['Car rental', '租车服务'],
  ['Wi-Fi in public areas', '公共区 Wi-Fi'],
  ['Fitness room', '健身房']
])

const buildPropertyCorpus = (property) =>
  [
    property?.propertyName,
    property?.city,
    property?.district,
    property?.address,
    property?.description,
    ...(Array.isArray(property?.facilities) ? property.facilities : [])
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

const localizeDistrictLabel = (value) => {
  const text = cleanInlineText(value)
  if (!text) return ''

  const lowered = text.toLowerCase()
  const exactAlias = DISTRICT_LABELS.find(({ tokens }) => tokens.some((token) => lowered === token))
  if (exactAlias) return exactAlias.label

  const partialAlias = DISTRICT_LABELS.find(({ tokens }) => tokens.some((token) => lowered.includes(token)))
  if (partialAlias) return partialAlias.label

  return text
    .replace(/\bdistrict\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim()
}

const localizeLocationCopy = (value) => {
  let text = sanitizeLocationLabel(value)
  if (!text) return ''

  AREA_LABELS.forEach(({ label, tokens }) => {
    tokens.forEach((token) => {
      const pattern = new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'ig')
      text = text.replace(pattern, label)
    })
  })

  DISTRICT_LABELS.forEach(({ label, tokens }) => {
    tokens.forEach((token) => {
      const pattern = new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'ig')
      text = text.replace(pattern, label)
    })
  })

  return text.replace(/\s+/g, ' ').trim()
}

const localizeFacilityLabel = (value) => {
  const text = cleanInlineText(value)
  if (!text) return ''
  if (FACILITY_LABELS.has(text)) return FACILITY_LABELS.get(text)
  if (/^\d+\s*Outdoor swimming pools?$/i.test(text)) return text.startsWith('2') ? '双泳池' : '室外泳池'
  if (/^Outdoor swimming pool$/i.test(text)) return '室外泳池'
  if (/^Restaurants?$/i.test(text) || /^\d+\s*Restaurants?$/i.test(text)) return '餐厅'
  if (/^Caf[eé]$/i.test(text)) return '咖啡厅'
  if (/^Bar$/i.test(text)) return '酒吧'
  return text
}

const inferAreaLabel = (property) => {
  const corpus = buildPropertyCorpus(property)
  const area = AREA_LABELS.find(({ tokens }) => tokens.some((token) => corpus.includes(token.toLowerCase())))
  if (area) return area.label
  return localizeDistrictLabel(property?.district || '')
}

const localizePropertyFacilities = (facilities, limit = 5) =>
  sanitizeChipList((Array.isArray(facilities) ? facilities : []).map((item) => localizeFacilityLabel(item)), limit)

const localizeChipItems = (items) =>
  (Array.isArray(items) ? items : [items]).map((item) => localizeFacilityLabel(item))

const getPropertyIntent = (queryText = '') => {
  const value = String(queryText || '').toLowerCase()
  return {
    seaView: /海景|海边|沙滩|ocean|sea view|seaview|beach|bay|coast/.test(value),
    family: /亲子|儿童|kids|family/.test(value),
    business: /商务|出差|会务|商旅|business/.test(value),
    airport: /机场|转机|航班|airport/.test(value),
    resort: /度假|vacation|resort/.test(value),
    luxury: /高端|奢华|豪华|luxury/.test(value),
    text: value
  }
}

const matchesAreaIntent = (queryText = '', areaLabel = '') => {
  if (!queryText || !areaLabel) return false
  return queryText.includes(areaLabel.toLowerCase())
}

const scorePropertyForQuery = (property, query = {}) => {
  const corpus = buildPropertyCorpus(property)
  const areaLabel = inferAreaLabel(property)
  const intent = getPropertyIntent(query.queryText || `${query.city || ''} ${query.keyword || ''}`)
  let score = 0

  if (query.city && property?.city && property.city.includes(query.city)) score += 8
  if (query.keyword && corpus.includes(String(query.keyword).toLowerCase())) score += 16
  if (matchesAreaIntent(intent.text, areaLabel)) score += 22
  if (intent.seaView && /sea view|ocean|coast|beach|bay|海/.test(corpus)) score += 24
  if (intent.family && /kids|family|playground|water park|儿童|亲子/.test(corpus)) score += 18
  if (intent.business && /business|executive lounge|meeting|conference|商旅|会务/.test(corpus)) score += 16
  if (intent.airport && /airport|station|机场|接机|接站/.test(corpus)) score += 18
  if (intent.resort && /resort|vacation|bay|beach|海/.test(corpus)) score += 14
  if (intent.luxury && /marriott|swissôtel|spa|executive|luxury|豪华/.test(corpus)) score += 12
  if (property?.featured) score += 6

  const rating = Number(property?.rating)
  if (Number.isFinite(rating) && rating > 0) score += rating * 4

  return score
}

const sortPropertiesByQuery = (items, query = {}) =>
  [...(Array.isArray(items) ? items : [])].sort((left, right) => {
    const scoreDiff = scorePropertyForQuery(right, query) - scorePropertyForQuery(left, query)
    if (scoreDiff) return scoreDiff

    const ratingDiff = Number(right?.rating || 0) - Number(left?.rating || 0)
    if (ratingDiff) return ratingDiff

    return Number(right?.featured || 0) - Number(left?.featured || 0)
  })

const deriveRecommendationTitle = (query = {}) => {
  const queryText = String(query.queryText || `${query.city || ''} ${query.keyword || ''}`).trim()
  const city = query.city || inferCityFromText(queryText)

  if (/海景|海边|沙滩/.test(queryText)) return compactCategoryName(`${city || ''}海景推荐`, '海景推荐')
  if (/亲子|儿童/.test(queryText)) return compactCategoryName(`${city || ''}亲子推荐`, '亲子推荐')
  if (/商务|出差|商旅/.test(queryText)) return compactCategoryName(`${city || ''}商务推荐`, '商务推荐')
  if (/机场|转机|航班/.test(queryText)) return compactCategoryName(`${city || ''}机场周边推荐`, '机场周边推荐')

  return compactCategoryName(city ? `${city}精选推荐` : '精选推荐', '精选推荐')
}

const buildPropertyLocation = (property) => {
  const areaLabel = inferAreaLabel(property)
  const districtLabel = localizeDistrictLabel(property?.district || '')
  return [property?.city, areaLabel || districtLabel].filter(Boolean).join(' · ')
}

const buildPropertyTagList = (property, query = {}) => {
  const intent = getPropertyIntent(query.queryText || `${query.city || ''} ${query.keyword || ''}`)
  const areaLabel = inferAreaLabel(property)
  const facilities = localizePropertyFacilities(property?.facilities, 5)
  const tags = []

  if (intent.seaView) tags.push('海景度假')
  else if (intent.family) tags.push('亲子友好')
  else if (intent.business) tags.push('商务便捷')
  else if (intent.airport) tags.push('通勤方便')

  if (areaLabel) tags.push(areaLabel)
  if (Number(property?.rating || 0) >= 4.7) tags.push('高分口碑')
  if (property?.featured) tags.push('平台精选')

  return sanitizeChipList([...tags, ...facilities], 4)
}

const shouldRefreshPropertyHighlight = (value) => {
  const text = sanitizeHighlightText(value)
  if (!text) return true
  if (/[A-Za-z]/.test(text)) return true
  if (/district|outdoor|executive|parking|spa/i.test(text)) return true
  return false
}

const formatPriceLabel = (min, max) => {
  const low = Number(min)
  const high = Number(max)
  if (Number.isFinite(low) && low > 0 && Number.isFinite(high) && high > 0 && high !== low) {
    return `￥${Math.round(low)}-${Math.round(high)}`
  }
  if (Number.isFinite(low) && low > 0) return `￥${Math.round(low)}`
  if (Number.isFinite(high) && high > 0) return `￥${Math.round(high)}`
  return ''
}

const formatRating = (value) => {
  const rating = Number(value)
  if (!Number.isFinite(rating) || rating <= 0) return ''
  return rating.toFixed(1).replace(/\.0$/, '')
}

const buildPropertyDetailUrl = (propertyId, hash = '') => {
  const normalizedId = normalizePropertyId(propertyId)
  if (!normalizedId) return ''
  return `${PROPERTY_BASE_URL}/property/${normalizedId}${hash}`
}

const bookingExploreUrl = ({ propertyId, city, keyword } = {}) => {
  const propertyDetailUrl = buildPropertyDetailUrl(propertyId, '#rooms')
  if (propertyDetailUrl) return propertyDetailUrl
  const params = new URLSearchParams()
  if (city) params.set('city', city)
  if (keyword) params.set('keyword', keyword)
  const query = params.toString()
  return `${PROPERTY_BASE_URL}/simple-booking${query ? `?${query}` : ''}`
}

const getBadgeLabel = (hotel, categoryName = '') => {
  const candidates = [
    hotel.badgeLabel,
    hotel.city,
    sanitizeLocationLabel(hotel.location || '').split('·')[0],
    compactCategoryName(categoryName, '')
  ]
    .map((item) => cleanInlineText(item))
    .filter(Boolean)
  return candidates.find((item) => item.length <= 8) || '精选'
}

const normalizeHotelRecord = (hotel, categoryName = '') => {
  const name = sanitizeHotelName(hotel?.name || '')
  const rawLocation = localizeLocationCopy(hotel?.location || hotel?.address || '')
  const location = isPlaceholderLocation(rawLocation) ? '' : rawLocation
  const highlight = sanitizeHighlightText(hotel?.highlight || hotel?.summary || hotel?.description || '')
  const tags = sanitizeChipList(localizeChipItems(hotel?.tags || hotel?.highlights || highlight), 4)
  const facilities = sanitizeChipList(localizeChipItems(hotel?.facilities), 5).filter((item) => !tags.includes(item))
  const detailUrl = isUsableActionUrl(hotel?.detailUrl) ? String(hotel.detailUrl).trim() : ''
  const bookingUrl = isUsableActionUrl(hotel?.bookingUrl) ? String(hotel.bookingUrl).trim() : ''
  const propertyId =
    normalizePropertyId(hotel?.propertyId) ||
    extractPropertyIdFromUrl(detailUrl) ||
    extractPropertyIdFromUrl(bookingUrl)
  const matchedProperty = Boolean(
    hotel?.matchedProperty ||
    propertyId ||
    parseLocalPath(detailUrl)?.startsWith('/property/')
  )

  return {
    ...hotel,
    propertyId,
    name: name || '精选酒店',
    category: compactCategoryName(hotel?.category || categoryName),
    location,
    address: localizeLocationCopy(hotel?.address || ''),
    city: hotel?.city || inferCityFromText([name, location, highlight].join(' ')),
    highlight,
    tags,
    facilities,
    imageUrl: safeImage(hotel?.imageUrl || parseImageList(hotel?.images)[0] || ''),
    detailUrl,
    bookingUrl,
    detailLabel: hotel?.detailLabel || (matchedProperty ? '查看详情' : '查看同类房源'),
    bookingLabel: hotel?.bookingLabel || (matchedProperty ? '立即预订' : '去搜索预订'),
    matchedProperty,
    badgeLabel: getBadgeLabel(hotel, categoryName)
  }
}

const normalizeHotelCategories = (categories) =>
  (Array.isArray(categories) ? categories : [])
    .map((category) => ({
      ...category,
      name: compactCategoryName(category?.name),
      hotels: (Array.isArray(category?.hotels) ? category.hotels : [])
        .map((hotel) => normalizeHotelRecord(hotel, category?.name))
        .filter((hotel) => hotel.name)
    }))
    .filter((category) => category.hotels.length)

const buildRecommendationCategories = (recommendations) => {
  if (!recommendations?.cards?.length) return null
  const title = compactCategoryName(recommendations.title || '酒店推荐', '酒店推荐')
  return [
    {
      name: title,
      hotels: recommendations.cards.map((card) => normalizeHotelRecord({
        id: card.id || card.propertyId || '',
        propertyId:
          normalizePropertyId(card.propertyId) ||
          extractPropertyIdFromUrl(card.detailUrl || '') ||
          extractPropertyIdFromUrl(card.bookingUrl || '') ||
          '',
        category: title,
        name: card.name || '精选酒店',
        location: card.location || [card.city, card.district].filter(Boolean).join(' · '),
        address: card.address || '',
        city: card.city || inferCityFromText([card.location, card.address, card.name].join(' ')),
        highlight: card.summary || card.description || '',
        facilities: Array.isArray(card.facilities) ? card.facilities.slice(0, 5) : [],
        tags: Array.isArray(card.highlights) ? card.highlights.slice(0, 4) : [],
        priceLabel: card.priceLabel || formatPriceLabel(card.priceMin, card.priceMax),
        rating: formatRating(card.rating),
        imageUrl: safeImage(card.imageUrl),
        detailUrl: card.detailUrl || '',
        bookingUrl: card.bookingUrl || '',
        roomTypes: Array.isArray(card.roomTypes) ? card.roomTypes : [],
        detailLabel: '查看详情',
        bookingLabel: '立即预订',
        matchedProperty: Boolean(
          normalizePropertyId(card.propertyId) ||
          extractPropertyIdFromUrl(card.detailUrl || '') ||
          extractPropertyIdFromUrl(card.bookingUrl || '') ||
          parseLocalPath(card.detailUrl || '')?.startsWith('/property/')
        )
      }, title))
    }
  ]
}

const buildParsedCategories = (content) => {
  const parsed = parseHotelRecommendations(content)
  if (!parsed?.length) return null
  return parsed.map((category) => ({
    name: compactCategoryName(category.name),
    hotels: category.hotels.map((hotel) => normalizeHotelRecord({
      ...hotel,
      id: hotel.id || '',
      propertyId: hotel.propertyId || '',
      category: category.name,
      imageUrl: safeImage(hotel.imageUrl || ''),
      detailUrl: hotel.detailUrl || '',
      bookingUrl: hotel.bookingUrl || '',
      priceLabel: hotel.priceLabel || hotel.price || '',
      rating: hotel.rating ? String(hotel.rating) : '',
      tags: Array.isArray(hotel.tags) ? hotel.tags.slice(0, 4) : Array.isArray(hotel.facilities) ? hotel.facilities.slice(0, 4) : [],
      facilities: Array.isArray(hotel.facilities) ? hotel.facilities.slice(0, 5) : [],
      detailLabel: '查看详情',
      bookingLabel: '立即预订',
      matchedProperty: Boolean(hotel.propertyId)
    }, category.name))
  }))
}

const buildHotelCards = (message) => {
  if (Array.isArray(message?.hotelCards) && message.hotelCards.length) return normalizeHotelCategories(message.hotelCards)
  return buildRecommendationCategories(message?.recommendations) || buildParsedCategories(message?.content)
}

const getValidHotelCards = (categories) =>
  (Array.isArray(categories) ? categories : [])
    .flatMap((category) => category.hotels || [])
    .filter((hotel) => !isLowQualityHotelCard(hotel))

const isLowQualityHotelCard = (hotel) => {
  const name = sanitizeHotelName(hotel?.name || '')
  const location = sanitizeLocationLabel(hotel?.location || '')
  const highlight = sanitizeHighlightText(hotel?.highlight || '')
  const hasRealLink = isUsableActionUrl(hotel?.detailUrl) || isUsableActionUrl(hotel?.bookingUrl)
  const hasPropertyMatch = Boolean(hotel?.matchedProperty || hotel?.propertyId)

  if (!name) return true
  if (name.includes('|')) return true
  if (/^(?:以下是|推荐|酒店推荐|房源推荐|精选推荐|热门推荐|Top推荐)/i.test(name)) return true
  if (/共\d+家/.test(name)) return true
  if (name.length <= 4 && !hasPropertyMatch) return true
  if (isPlaceholderLocation(location) && !hasPropertyMatch) return true
  if (!location && !highlight && !hasPropertyMatch && !hasRealLink) return true
  if (!hasPropertyMatch && !hasRealLink && !highlight) return true
  return false
}

const hasUsableHotelCategories = (categories, { allowSingle = false } = {}) => {
  const hotels = (Array.isArray(categories) ? categories : []).flatMap((category) => category.hotels || [])
  if (!hotels.length) return false
  const validHotels = getValidHotelCards(categories)
  if (!validHotels.length) return false
  if (validHotels.length === 1) {
    if (!allowSingle) return false
    return Boolean(
      validHotels[0]?.matchedProperty ||
      validHotels[0]?.propertyId ||
      isUsableActionUrl(validHotels[0]?.detailUrl) ||
      isUsableActionUrl(validHotels[0]?.bookingUrl)
    )
  }
  return validHotels.length >= 2
}

const isRealPropertyHotelCard = (hotel) =>
  Boolean(
    hotel?.matchedProperty ||
    hotel?.propertyId ||
    parseLocalPath(hotel?.detailUrl || '')?.startsWith('/property/') ||
    parseLocalPath(hotel?.bookingUrl || '')?.startsWith('/property/')
  )

const getDistinctPropertyCount = (categories) => {
  const ids = (Array.isArray(categories) ? categories : [])
    .flatMap((category) => category.hotels || [])
    .map((hotel) => normalizePropertyId(hotel?.propertyId) || extractPropertyIdFromUrl(hotel?.detailUrl || '') || '')
    .filter(Boolean)

  return new Set(ids).size
}

const hasHealthyPropertyCoverage = (categories) => {
  const hotels = (Array.isArray(categories) ? categories : []).flatMap((category) => category.hotels || [])
  if (!hotels.length) return false

  const distinctPropertyCount = getDistinctPropertyCount(categories)
  if (!distinctPropertyCount) return false
  if (hotels.length <= 3) return distinctPropertyCount >= 1
  if (hotels.length <= 6) return distinctPropertyCount >= 3
  return distinctPropertyCount / hotels.length >= 0.45
}

const resolveInitialHotelCards = (message) => {
  if (!message || message.role !== 'assistant' || message.isStreaming) return null

  if (Array.isArray(message.hotelCards) && message.hotelCards.length) {
    const normalized = normalizeHotelCategories(message.hotelCards)
    const isCurrentVersion = Number(message.hotelCardsVersion || 0) >= HOTEL_CARD_HYDRATION_VERSION
    const allRealPropertyCards = normalized
      .flatMap((category) => category.hotels || [])
      .every((hotel) => isRealPropertyHotelCard(hotel))
    const coverageHealthy = hasHealthyPropertyCoverage(normalized)

    return hasUsableHotelCategories(normalized) && coverageHealthy && (isCurrentVersion || allRealPropertyCards) ? normalized : null
  }

  const recommendationCards = buildRecommendationCategories(message.recommendations)
  if (hasUsableHotelCategories(recommendationCards)) return recommendationCards

  if (message.hotelCardsHydrated) {
    return recommendationCards || buildParsedCategories(message.content)
  }

  return null
}

const summarizePropertyHighlight = (property, query = {}) => {
  const intent = getPropertyIntent(query.queryText || `${query.city || ''} ${query.keyword || ''}`)
  const areaLabel = inferAreaLabel(property)
  const topFacilities = localizePropertyFacilities(property?.facilities, 2)
  const parts = []

  if (intent.seaView) {
    parts.push(areaLabel ? `${areaLabel}度假氛围更强` : '更适合海边度假')
  } else if (intent.family) {
    parts.push('更适合亲子出行')
  } else if (intent.business) {
    parts.push('商旅通勤更方便')
  } else if (intent.airport) {
    parts.push('往返机场更省心')
  } else if (property?.featured) {
    parts.push('平台精选')
  }

  if (!parts.length && areaLabel) parts.push(`靠近${areaLabel}`)
  if (topFacilities.length) parts.push(topFacilities.join('、'))
  if (Number(property?.rating || 0) >= 4.7) parts.push('住客口碑稳定')

  return parts.join('，')
}

const buildPropertyCategoriesFromSearch = (items, query = {}) => {
  const properties = sortPropertiesByQuery(Array.isArray(items) ? items.filter(Boolean) : [], query).slice(0, 6)
  if (!properties.length) return null

  const title = deriveRecommendationTitle(query)
  return [
    {
      name: title,
      hotels: properties.map((property) =>
        normalizeHotelRecord(
          {
            id: property.id,
            propertyId: property.id,
            category: title,
            name: property.propertyName || '精选酒店',
            location: buildPropertyLocation(property),
            address: property.address || '',
            city: property.city || query.city || '',
            highlight: summarizePropertyHighlight(property, query),
            facilities: localizePropertyFacilities(property.facilities, 5),
            tags: buildPropertyTagList(property, query),
            priceLabel: formatPriceLabel(property.priceRangeMin, property.priceRangeMax),
            rating: formatRating(property.rating),
            imageUrl: parseImageList(property.images)[0] || '',
            detailUrl: buildPropertyDetailUrl(property.id),
            bookingUrl: bookingExploreUrl({ propertyId: property.id }),
            detailLabel: '查看详情',
            bookingLabel: '立即预订',
            matchedProperty: true,
            badgeLabel: inferAreaLabel(property) || property.city || query.city || '精选'
          },
          title
        )
      )
    }
  ]
}

const normalizeMessage = (message) => {
  if (!message || typeof message !== 'object') return null
  const role = String(message.role || '').trim()
  if (!role) return null
  const isStreaming = Boolean(message.isStreaming)

  return {
    ...message,
    role,
    isStreaming,
    content: typeof message.content === 'string' ? message.content : message.content == null ? '' : String(message.content),
    recommendations: message.recommendations || null,
    pendingAction: message.pendingAction || null,
    createdAt: Number.isFinite(message.createdAt) ? message.createdAt : Date.now(),
    hotelCards: role === 'assistant' ? resolveInitialHotelCards(message) : null,
    hotelCardsHydrated: Boolean(message.hotelCardsHydrated),
    hotelCardsVersion: Number.isFinite(message.hotelCardsVersion) ? message.hotelCardsVersion : 0,
    error: Boolean(message.error)
  }
}

const cloneMessages = (list) => (Array.isArray(list) ? list.map(normalizeMessage).filter(Boolean) : [])

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`

const hasHotelCards = (item) => Array.isArray(item?.hotelCards) && item.hotelCards.length > 0

const getHotelCategories = (item) => (Array.isArray(item?.hotelCards) && item.hotelCards.length ? item.hotelCards : null)

const getHotelCount = (item) => (getHotelCategories(item) || []).reduce((sum, category) => sum + (category.hotels?.length || 0), 0)

const getHotelCities = (item) => {
  const cities = (getHotelCategories(item) || [])
    .flatMap((category) => category.hotels || [])
    .map((hotel) => hotel.city || inferCityFromText([hotel.location, hotel.address, hotel.name].join(' ')))
    .filter(Boolean)

  return cities.filter((city, index) => cities.indexOf(city) === index)
}

const getHotelSummary = (item) => {
  const count = getHotelCount(item)
  if (!count) return ''
  const cities = getHotelCities(item)
  if (cities.length === 1) return `已为您筛出 ${count} 家${cities[0]}可查看酒店，卡片里可直接查看详情或继续预订。`
  return `已为您筛出 ${count} 家可查看酒店，卡片里可直接查看详情或继续预订。`
}

const getHotelSubtitle = (item) => {
  if (item?.recommendations?.subtitle) return item.recommendations.subtitle
  const count = getHotelCount(item)
  return count ? `${count} 家可查看酒店` : ''
}

const getRenderableContent = (item) => {
  if (!item) return ''
  if (hasHotelCards(item)) return getHotelSummary(item)
  return item.content || ''
}

const persistCurrentConversation = (titleOverride = null) => {
  if (!conversationId.value) return
  const title =
    titleOverride ||
    conversations.value.find((item) => item.id === conversationId.value)?.title ||
    messages.value.find((item) => item.role === 'user')?.content?.slice(0, 24) ||
    '新对话'

  save({
    id: conversationId.value,
    title,
    updatedAt: Date.now(),
    messages: cloneMessages(messages.value)
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

const autoGrow = () => {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

const ensureConversationId = () => {
  if (!conversationId.value) {
    conversationId.value = crypto?.randomUUID?.() || createId('conv')
  }
}

const findBestPropertyMatch = (hotel, properties) => {
  if (!Array.isArray(properties) || !properties.length) return null
  const hotelNames = buildHotelNameVariants(hotel.name)
  const hotelCity = hotel.city || inferCityFromText([hotel.location, hotel.address].join(' '))
  const hotelLocation = normalizeChineseVariants(String(hotel.location || '').toLowerCase())
  const hotelAddress = normalizeChineseVariants(String(hotel.address || '').toLowerCase())

  let best = null
  let bestScore = -1

  for (const property of properties) {
    const propertyNames = buildHotelNameVariants(property.propertyName)
    const propertyName = propertyNames[0] || ''
    const propertyDistrict = normalizeChineseVariants(String(property.district || '').toLowerCase())
    let score = 0

    if (!propertyName) continue

    hotelNames.forEach((hotelName) => {
      propertyNames.forEach((candidate) => {
        if (!hotelName || !candidate) return
        if (candidate === hotelName) score = Math.max(score, 100)
        else if (candidate.includes(hotelName) || hotelName.includes(candidate)) score = Math.max(score, 76)
        else {
          const sharedLength = Math.min(candidate.length, hotelName.length)
          if (sharedLength >= 4) {
            const overlap =
              [...candidate].filter((char) => hotelName.includes(char)).length / Math.max(sharedLength, 1)
            if (overlap >= 0.72) score = Math.max(score, 58)
          }
        }
      })
    })

    if (hotelCity && property.city && property.city.includes(hotelCity)) score += 10
    if (hotelLocation && propertyDistrict && (hotelLocation.includes(propertyDistrict) || propertyDistrict.includes(hotelLocation))) score += 12
    if (hotelAddress && propertyDistrict && hotelAddress.includes(propertyDistrict)) score += 6
    if (hotelLocation && propertyName && (hotelLocation.includes(propertyName) || propertyName.includes(hotelLocation))) score += 4

    if (score > bestScore) {
      bestScore = score
      best = property
    }
  }

  return bestScore >= 50 ? best : null
}

const searchProperties = async (city, keyword) => {
  const cacheKey = JSON.stringify([city || '', keyword || ''])
  if (propertySearchCache.has(cacheKey)) return propertySearchCache.get(cacheKey)

  try {
    const { data } = await propertyApi.search({
      city: city || undefined,
      keyword: keyword || undefined,
      page: 1,
      size: 8
    })
    const items = Array.isArray(data?.items) ? data.items : []
    propertySearchCache.set(cacheKey, items)
    return items
  } catch {
    propertySearchCache.set(cacheKey, [])
    return []
  }
}

const getCityProperties = async (city) => {
  const normalizedCity = String(city || '').trim()
  if (!normalizedCity) return []
  if (cityPropertyCache.has(normalizedCity)) return cityPropertyCache.get(normalizedCity)

  try {
    const { data } = await propertyApi.getByCity(normalizedCity)
    const items = Array.isArray(data) ? data : []
    cityPropertyCache.set(normalizedCity, items)
    return items
  } catch {
    cityPropertyCache.set(normalizedCity, [])
    return []
  }
}

const mergePropertySearchResults = (...groups) => {
  const merged = []
  const seen = new Set()

  groups.flat(Infinity).forEach((item) => {
    const id = normalizePropertyId(item?.id)
    if (!id || seen.has(id)) return
    seen.add(id)
    merged.push(item)
  })

  return merged
}

const buildSearchFallbackCategories = async (userPrompt = '', assistantText = '') => {
  const city = inferCityFromText([userPrompt, assistantText].join(' '))
  const promptText = String(userPrompt || '').trim()
  const analysisText = `${userPrompt} ${assistantText}`.trim()
  const queryText = promptText || analysisText
  const keywordHints = ['机场', '口岸', '迪士尼', '外滩', '华强北', '万象城', '亚龙湾', '大东海', '海棠湾']
  const keyword = keywordHints.find((item) => analysisText.includes(item)) || ''

  const plans = []
  if (city && keyword) plans.push({ city, keyword, queryText })
  if (city) plans.push({ city, keyword: '', queryText })
  if (!city && keyword) plans.push({ city: '', keyword, queryText })

  const collected = []
  for (const plan of plans) {
    const items = await searchProperties(plan.city, plan.keyword)
    if (items.length) collected.push(items)
  }

  const mergedItems = mergePropertySearchResults(...collected)
  if (!mergedItems.length && city) {
    const cityItems = await getCityProperties(city)
    if (cityItems.length) {
      return buildPropertyCategoriesFromSearch(cityItems, { city, keyword, queryText })
    }
    return null
  }
  if (!mergedItems.length) return null

  return buildPropertyCategoriesFromSearch(mergedItems, { city, keyword, queryText })
}

const toMatchedHotelCard = (hotel, match, fallbackText = '', city = '') => ({
  ...hotel,
  propertyId: hotel.propertyId || match.id,
  city: city || hotel.city || match.city || '',
  location: hotel.location || buildPropertyLocation(match),
  address: hotel.address || match.address || '',
  imageUrl: safeImage(hotel.imageUrl || parseImageList(match.images)[0] || ''),
  detailUrl: buildPropertyDetailUrl(match.id),
  bookingUrl: bookingExploreUrl({ propertyId: match.id }),
  priceLabel: hotel.priceLabel || formatPriceLabel(match.priceRangeMin, match.priceRangeMax),
  rating: hotel.rating || formatRating(match.rating),
  highlight: shouldRefreshPropertyHighlight(hotel.highlight)
    ? summarizePropertyHighlight(match, { city, keyword: hotel.name || '', queryText: `${hotel.name || ''} ${fallbackText || ''}` })
    : hotel.highlight,
  facilities: localizePropertyFacilities(hotel.facilities?.length ? hotel.facilities : match.facilities, 5),
  tags: hotel.tags?.length
    ? sanitizeChipList(localizeChipItems(hotel.tags), 4)
    : buildPropertyTagList(match, { city, keyword: hotel.name || '', queryText: `${hotel.name || ''} ${fallbackText || ''}` }),
  detailLabel: '查看详情',
  bookingLabel: '立即预订',
  matchedProperty: true,
  badgeLabel: inferAreaLabel(match) || getBadgeLabel({ ...hotel, city: city || match.city || '' }, hotel.category)
})

const enrichHotel = async (hotel, fallbackText = '') => {
  const city = hotel.city || inferCityFromText([hotel.location, hotel.address, fallbackText].join(' '))
  const keyword = hotel.name || ''
  const directResults = await searchProperties(city, keyword)
  const cityResults = city ? await getCityProperties(city) : []
  const globalResults = directResults.length || cityResults.length ? [] : await searchProperties('', keyword)
  const results = mergePropertySearchResults(directResults, cityResults, globalResults)
  const match = findBestPropertyMatch({ ...hotel, city }, results)

  if (!match) {
    const cityFallback = sortPropertiesByQuery(cityResults, {
      city,
      keyword,
      queryText: `${hotel.name || ''} ${hotel.location || ''} ${hotel.category || ''} ${fallbackText || ''}`
    })[0]

    if (cityFallback) {
      return toMatchedHotelCard(hotel, cityFallback, fallbackText, city)
    }

    return {
      ...hotel,
      city,
      imageUrl: safeImage(hotel.imageUrl || ''),
      detailUrl: hotel.detailUrl || bookingExploreUrl({ city, keyword: hotel.name }),
      bookingUrl: hotel.bookingUrl || bookingExploreUrl({ city, keyword: hotel.name }),
      detailLabel: '查看同类房源',
      bookingLabel: '去搜索预订',
      matchedProperty: false,
      badgeLabel: getBadgeLabel({ ...hotel, city }, hotel.category)
    }
  }

  return toMatchedHotelCard(hotel, match, fallbackText, city)
}

const hydrateMessageHotels = async (messageId) => {
  const index = messages.value.findIndex((message) => message.id === messageId)
  if (index < 0) return
  const current = messages.value[index]
  if (current.role !== 'assistant') return

  const userPrompt =
    [...messages.value]
      .slice(0, index)
      .reverse()
      .find((message) => message?.role === 'user')?.content || ''

  let categories = current.hotelCards?.length ? normalizeHotelCategories(current.hotelCards) : null
  const needsSearchRebuild =
    !hasHealthyPropertyCoverage(categories) ||
    Number(current.hotelCardsVersion || 0) < HOTEL_CARD_HYDRATION_VERSION

  if (
    current.hotelCardsHydrated &&
    current.hotelCardsVersion === HOTEL_CARD_HYDRATION_VERSION &&
    hasUsableHotelCategories(categories, { allowSingle: true }) &&
    hasHealthyPropertyCoverage(categories)
  ) return

  if (needsSearchRebuild || !hasUsableHotelCategories(categories)) {
    const fallbackCategories = await buildSearchFallbackCategories(userPrompt, current.content || '')
    if (fallbackCategories?.length) {
      categories = fallbackCategories
    } else {
      const parsedCategories = buildParsedCategories(current.content || '')
      if (parsedCategories?.length) {
        categories = parsedCategories
      }
    }
  }

  if (!categories?.length) return

  const hydrated = await Promise.all(
    categories.map(async (category) => ({
      ...category,
      hotels: await Promise.all((category.hotels || []).map((hotel) => enrichHotel(hotel, current.content)))
    }))
  )

  const latest = messages.value.findIndex((message) => message.id === messageId)
  if (latest < 0) return
  messages.value[latest] = {
    ...messages.value[latest],
    hotelCards: hydrated,
    hotelCardsHydrated: true,
    hotelCardsVersion: HOTEL_CARD_HYDRATION_VERSION
  }
  messages.value = [...messages.value]
  persistCurrentConversation()
}

const queueHotelHydration = (messageId) => {
  void hydrateMessageHotels(messageId)
}

const loadDemoConversation = () => {
  conversationId.value = 'assistant-preview-demo'
  messages.value = cloneMessages([
    {
      id: 'demo-user-1',
      role: 'user',
      content: '广东预算1000元推荐酒店',
      createdAt: Date.now() - 1000
    },
    {
      id: 'demo-assistant-1',
      role: 'assistant',
      content: demoAssistantAnswer,
      createdAt: Date.now(),
      recommendations: null,
      pendingAction: null
    }
  ])
  pendingAction.value = null
  messages.value.forEach((message) => queueHotelHydration(message.id))
}

const resetConversation = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  conversationId.value = ''
  draft.value = ''
  loading.value = false
  errorText.value = ''
  pendingAction.value = null
  streamingId.value = ''
  messages.value = []
  if (isPreviewMode.value) {
    conversationId.value = 'assistant-preview-demo'
    loadDemoConversation()
  }
  nextTick(autoGrow)
}

const activateConversation = async (id) => {
  if (isPreviewMode.value) return
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  conversationId.value = id
  draft.value = ''
  loading.value = false
  errorText.value = ''
  pendingAction.value = null
  streamingId.value = ''
  messages.value = []

  if (window.innerWidth < 920) sidebarOpen.value = false

  const local = getById(id)
  if (local?.messages?.length) {
    messages.value = cloneMessages(local.messages)
    pendingAction.value = messages.value[messages.value.length - 1]?.pendingAction || null
    messages.value.forEach((message) => queueHotelHydration(message.id))
    scrollToBottom()
    return
  }

  try {
    const remote = await getAssistantConversationMessages(id)
    messages.value = cloneMessages(remote)
    pendingAction.value = messages.value[messages.value.length - 1]?.pendingAction || null
    persistCurrentConversation(local?.title || '历史对话')
    messages.value.forEach((message) => queueHotelHydration(message.id))
  } catch {
    errorText.value = '历史对话加载失败'
  }
  scrollToBottom()
}

const deleteConversation = (id) => {
  if (isPreviewMode.value) return
  remove(id)
  if (favorites.value.includes(id)) toggleFavorite(id)
  if (conversationId.value === id) resetConversation()
}

const quickSend = (text) => {
  draft.value = text
  sendMessage()
}

const confirmPendingAction = async (action) => {
  try {
    await ElMessageBox.confirm(
      action.confirmation_text || '确认执行该操作？',
      '请确认',
      { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' }
    )
    draft.value = action.confirmation_text || draft.value
    await sendMessage(action)
  } catch (error) {
    if (error !== 'cancel') errorText.value = '确认流程未完成'
  }
}

const sendMessage = async (actionOverride = null) => {
  const message = draft.value.trim()
  if (!message || loading.value) return

  if (!isPreviewMode.value) ensureConversationId()
  const currentPendingAction = actionOverride || pendingAction.value
  errorText.value = ''
  if (actionOverride) pendingAction.value = null

  if (!isPreviewMode.value) {
    save({ id: conversationId.value, title: message.slice(0, 24) || '新对话', updatedAt: Date.now() })
  }
  messages.value.push(normalizeMessage({ id: createId('user'), role: 'user', content: message, createdAt: Date.now() }))
  draft.value = ''
  nextTick(autoGrow)
  loading.value = true

  const assistantId = createId('assistant')
  streamingId.value = assistantId
  messages.value.push(normalizeMessage({ id: assistantId, role: 'assistant', content: '', createdAt: Date.now(), isStreaming: true }))

  const controller = new AbortController()
  abortController.value = controller
  let receivedDoneEvent = false

  try {
    await streamAssistantChat({
      message,
      conversationId: conversationId.value,
      userContext: userContext.value,
      pendingAction: currentPendingAction,
      signal: controller.signal,
      onEvent(event) {
        if (event.type === 'meta') {
          if (event.conversationId && !isPreviewMode.value) conversationId.value = event.conversationId
          return
        }
        if (event.type === 'chunk') {
          const index = messages.value.findIndex((item) => item.id === assistantId)
          if (index >= 0) {
            messages.value[index] = normalizeMessage({
              ...messages.value[index],
              isStreaming: true,
              content: `${messages.value[index].content || ''}${String(event.content || '')}`
            })
            messages.value = [...messages.value]
          }
          return
        }
        if (event.type === 'done') {
          receivedDoneEvent = true
          const index = messages.value.findIndex((item) => item.id === assistantId)
          const nextPending = event.pendingAction || null
          const answer =
            String(event.answer || '') ||
            (index >= 0 ? messages.value[index].content : '') ||
            'AI 没有返回内容。'

          pendingAction.value = nextPending

          if (index >= 0) {
            messages.value[index] = normalizeMessage({
              ...messages.value[index],
              isStreaming: false,
              content: answer,
              recommendations: event.recommendations || null,
              pendingAction: nextPending,
              hotelCardsHydrated: false
            })
            messages.value = [...messages.value]
            queueHotelHydration(assistantId)
          }

          if (!isPreviewMode.value) persistCurrentConversation(message.slice(0, 24) || '新对话')
          return
        }
        if (event.type === 'error') throw new Error(String(event.error || '请求失败'))
      }
    })

    if (!receivedDoneEvent) {
      const index = messages.value.findIndex((item) => item.id === assistantId)
      if (index >= 0) {
        const fallbackAnswer = String(messages.value[index].content || '').trim() || 'AI 没有返回内容。'
        messages.value[index] = normalizeMessage({
          ...messages.value[index],
          isStreaming: false,
          content: fallbackAnswer,
          recommendations: messages.value[index].recommendations || null,
          pendingAction: messages.value[index].pendingAction || null,
          hotelCardsHydrated: false
        })
        messages.value = [...messages.value]
        queueHotelHydration(assistantId)
      }

      if (!isPreviewMode.value) persistCurrentConversation(message.slice(0, 24) || '新对话')
    }
  } catch {
    const index = messages.value.findIndex((item) => item.id === assistantId)
    if (index >= 0) {
      messages.value[index] = normalizeMessage({
        ...messages.value[index],
        isStreaming: false,
        content: '抱歉，这次没有顺利完成。请稍后再试。',
        error: true
      })
      messages.value = [...messages.value]
    }
    errorText.value = 'AI 服务暂时不可用，请稍后重试。'
  } finally {
    loading.value = false
    streamingId.value = ''
    abortController.value = null
  }
}

const syncUser = () => {
  userContext.value = readAssistantUserContext()
}

watch(
  () => [messages.value.length, loading.value, messages.value[messages.value.length - 1]?.content?.length || 0],
  scrollToBottom
)

onMounted(async () => {
  syncUser()
  resetConversation()
  window.addEventListener('user-changed', syncUser)
  window.addEventListener('storage', syncUser)
  if (window.innerWidth < 920) sidebarOpen.value = false
  if (isPreviewMode.value) return
  try {
    const ids = await getAssistantConversationIds()
    syncRemote(ids)
  } catch {
    // ignore offline
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('user-changed', syncUser)
  window.removeEventListener('storage', syncUser)
})
</script>

<style scoped>
.concierge {
  --astra-primary: #c97e56;
  --astra-primary-soft: #f5f1ec;
  --astra-bg: #faf9f7;
  --astra-text: #2d2a26;
  --astra-text-soft: #8b8178;
  --astra-line: rgba(45, 42, 38, 0.07);
  --astra-user-bubble: #f3e1d6;
  --astra-ease: cubic-bezier(0.22, 1, 0.36, 1);

  position: fixed;
  inset: 0;
  display: flex;
  background: var(--astra-bg);
  color: var(--astra-text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
}

.side {
  width: 280px;
  flex-shrink: 0;
  background: var(--astra-bg);
  transition: width 0.28s var(--astra-ease), margin-left 0.28s var(--astra-ease);
  overflow: hidden;
}

.side--hidden {
  width: 0;
  margin-left: 0;
}

.side__inner {
  width: 280px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 26px 18px 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 12px;
  transition: opacity 0.18s var(--astra-ease);
}

.brand:hover {
  opacity: 0.7;
}

.brand__mark {
  width: 38px;
  height: 38px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(140deg, #d9966f 0%, var(--astra-primary) 100%);
  box-shadow: 0 8px 20px rgba(201, 126, 86, 0.28);
}

.brand__mark svg {
  width: 21px;
  height: 21px;
}

.brand__copy {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand__copy strong {
  font-size: 16px;
  font-weight: 650;
}

.brand__copy span {
  font-size: 11.5px;
  color: var(--astra-text-soft);
  letter-spacing: 0.04em;
}

.new-chat {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 13px 16px;
  border: none;
  border-radius: 15px;
  background: #fff;
  color: var(--astra-text);
  font-size: 14px;
  font-weight: 550;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(45, 42, 38, 0.04);
  transition: transform 0.2s var(--astra-ease), box-shadow 0.2s var(--astra-ease);
}

.new-chat svg {
  width: 17px;
  height: 17px;
  color: var(--astra-primary);
}

.new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(201, 126, 86, 0.16);
}

.side__group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}

.side__group--grow {
  flex: 1;
}

.side__label {
  margin: 0 0 2px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--astra-text-soft);
}

.side__empty {
  margin: 0;
  padding: 12px 10px;
  font-size: 13px;
  color: var(--astra-text-soft);
}

.conv-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.conv {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border: none;
  border-radius: 11px;
  background: transparent;
  color: var(--astra-text);
  font-size: 13.5px;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s var(--astra-ease);
}

.conv:hover {
  background: rgba(201, 126, 86, 0.07);
}

.conv--active {
  background: var(--astra-user-bubble);
}

.conv__star {
  color: var(--astra-primary);
  font-size: 12px;
  flex-shrink: 0;
}

.conv__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv__actions {
  display: none;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.conv:hover .conv__actions {
  display: flex;
}

.conv__icon {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  color: var(--astra-text-soft);
  font-size: 12px;
  transition: color 0.18s, background 0.18s;
}

.conv__icon svg {
  width: 14px;
  height: 14px;
}

.conv__icon:hover {
  background: rgba(45, 42, 38, 0.08);
  color: var(--astra-text);
}

.conv__icon--on {
  color: var(--astra-primary);
}

.user {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px;
  border-radius: 15px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(45, 42, 38, 0.04);
}

.user__avatar {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 14px;
  font-weight: 650;
  background: linear-gradient(140deg, #d9966f, var(--astra-primary));
  flex-shrink: 0;
}

.user__copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user__copy strong {
  font-size: 13.5px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user__copy span {
  font-size: 11.5px;
  color: var(--astra-text-soft);
}

.user__cog {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: var(--astra-text-soft);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.user__cog svg {
  width: 17px;
  height: 17px;
}

.user__cog:hover {
  background: var(--astra-primary-soft);
  color: var(--astra-primary);
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--astra-bg);
  border-left: 1px solid var(--astra-line);
}

.topbar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 28px;
  flex-shrink: 0;
}

.topbar__menu {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 11px;
  background: transparent;
  color: var(--astra-text-soft);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.topbar__menu svg {
  width: 20px;
  height: 20px;
}

.topbar__menu:hover {
  background: var(--astra-primary-soft);
  color: var(--astra-primary);
}

.topbar__title {
  text-align: center;
  flex: 1;
}

.topbar__title h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.topbar__spark {
  color: var(--astra-primary);
  font-size: 13px;
}

.topbar__title p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--astra-text-soft);
}

.topbar__spacer {
  width: 38px;
  flex-shrink: 0;
}

.stage {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 0 260px;
}

.stage--welcome {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-bottom: 210px;
}

.stage::-webkit-scrollbar {
  width: 9px;
}

.stage::-webkit-scrollbar-thumb {
  background: rgba(201, 126, 86, 0.18);
  border-radius: 999px;
}

.welcome {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 760px;
  padding: 0 24px;
  animation: rise 0.6s var(--astra-ease) both;
}

.welcome__halo {
  position: absolute;
  top: -60px;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(201, 126, 86, 0.12), transparent 68%);
  pointer-events: none;
}

.welcome__orb {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  font-size: 30px;
  color: #fff;
  background: linear-gradient(140deg, #e0a47c 0%, var(--astra-primary) 100%);
  box-shadow: 0 18px 40px rgba(201, 126, 86, 0.32);
  margin-bottom: 26px;
}

.welcome__title {
  margin: 0;
  font-size: 34px;
  font-weight: 680;
}

.welcome__sub {
  margin: 14px 0 0;
  font-size: 16px;
  line-height: 1.6;
  color: var(--astra-text-soft);
  max-width: 520px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 38px;
}

.chip {
  padding: 12px 22px;
  border: 1px solid var(--astra-line);
  border-radius: 999px;
  background: #fff;
  color: var(--astra-text);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(45, 42, 38, 0.03);
  transition: transform 0.2s var(--astra-ease), box-shadow 0.2s var(--astra-ease), border-color 0.2s var(--astra-ease);
}

.chip:hover {
  transform: translateY(-2px);
  border-color: rgba(201, 126, 86, 0.4);
  box-shadow: 0 8px 22px rgba(201, 126, 86, 0.16);
}

.thread {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 26px;
}

.row {
  display: flex;
  animation: rise 0.4s var(--astra-ease) both;
}

.row--user {
  justify-content: flex-end;
}

.row--ai {
  gap: 13px;
  align-items: flex-start;
}

.ai-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 11px;
  display: grid;
  place-items: center;
  font-size: 15px;
  color: #fff;
  background: linear-gradient(140deg, #e0a47c, var(--astra-primary));
  box-shadow: 0 6px 16px rgba(201, 126, 86, 0.24);
  margin-top: 2px;
}

.bubble {
  max-width: 100%;
  font-size: 15px;
  line-height: 1.72;
}

.bubble--user {
  padding: 13px 18px;
  border-radius: 20px 20px 6px 20px;
  background: var(--astra-user-bubble);
  color: var(--astra-text);
  max-width: 76%;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble--ai {
  flex: 1;
  min-width: 0;
  padding: 16px 20px;
  border-radius: 6px 20px 20px 20px;
  background: #fff;
  box-shadow: 0 4px 22px rgba(45, 42, 38, 0.05);
}

.bubble--error {
  background: #fdf3f0;
}

.prose {
  word-break: break-word;
}

.prose--summary {
  color: var(--astra-text-soft);
  font-size: 14px;
  line-height: 1.7;
}

.prose :deep(strong) {
  font-weight: 650;
}

.prose :deep(em) {
  font-style: italic;
}

.prose :deep(code) {
  padding: 2px 7px;
  border-radius: 7px;
  background: var(--astra-primary-soft);
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.88em;
  color: var(--astra-primary);
}

.prose :deep(a) {
  color: var(--astra-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.dots {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--astra-primary);
  opacity: 0.5;
  animation: blink 1.3s infinite ease-in-out;
}

.dots span:nth-child(2) {
  animation-delay: 0.18s;
}

.dots span:nth-child(3) {
  animation-delay: 0.36s;
}

.recos {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(45, 42, 38, 0.06);
}

.recos__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.recos__title {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}

.recos__sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--astra-text-soft);
}

.topbar__preview-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(201, 126, 86, 0.12);
  color: var(--astra-primary);
  font-size: 12px;
  font-weight: 700;
}

.pending {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--astra-primary-soft);
}

.pending__copy strong {
  font-size: 13.5px;
  font-weight: 620;
}

.pending__copy p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--astra-text);
}

.pending__impact {
  color: var(--astra-text-soft) !important;
}

.pending__btn {
  flex-shrink: 0;
  padding: 9px 18px;
  border: none;
  border-radius: 11px;
  background: var(--astra-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.composer {
  position: absolute;
  inset: auto 0 0;
  padding: 0 24px 26px;
  background: linear-gradient(180deg, rgba(250, 249, 247, 0) 0%, var(--astra-bg) 42%);
  pointer-events: none;
}

.composer__glass {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 64px;
  padding: 0 10px 0 16px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 40px rgba(45, 42, 38, 0.1);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  pointer-events: auto;
}

.composer__icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--astra-text-soft);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.composer__icon svg {
  width: 20px;
  height: 20px;
}

.composer__icon:hover {
  background: var(--astra-primary-soft);
  color: var(--astra-primary);
}

.composer__input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  resize: none;
  outline: none;
  font: inherit;
  font-size: 15px;
  line-height: 1.5;
  color: var(--astra-text);
  padding: 8px 4px;
  max-height: 160px;
}

.composer__input::placeholder {
  color: var(--astra-text-soft);
}

.composer__send {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border: none;
  border-radius: 14px;
  background: linear-gradient(140deg, #d9966f, var(--astra-primary));
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(201, 126, 86, 0.3);
  transition: transform 0.18s var(--astra-ease), opacity 0.18s;
}

.composer__send svg {
  width: 21px;
  height: 21px;
}

.composer__send:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.03);
}

.composer__send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.composer__err {
  max-width: 980px;
  margin: 10px auto 0;
  font-size: 12.5px;
  color: #c0573f;
  text-align: center;
  pointer-events: auto;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.85);
  }

  40% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 920px) {
  .side {
    position: absolute;
    z-index: 30;
    height: 100%;
    box-shadow: 12px 0 40px rgba(45, 42, 38, 0.12);
  }

  .side--hidden {
    box-shadow: none;
  }

  .thread,
  .composer__glass,
  .composer__err {
    max-width: 100%;
  }

  .welcome__title {
    font-size: 28px;
  }
}

@media (max-width: 560px) {
  .topbar {
    padding: 14px 16px;
  }

  .thread {
    padding: 16px;
  }

  .composer {
    padding: 0 12px 16px;
  }

  .stage {
    padding-bottom: 220px;
  }

  .bubble--user {
    max-width: 86%;
  }

  .chips {
    gap: 9px;
  }

  .chip {
    padding: 10px 16px;
    font-size: 13px;
  }
}
</style>
