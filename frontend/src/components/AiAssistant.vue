<template>
  <div class="assistant-shell" :class="{ 'assistant-shell--page': isPageMode }">
    <transition name="assistant-panel">
      <section
        v-if="isPageMode || expanded"
        class="assistant-panel"
        :class="{ 'assistant-panel--page': isPageMode }"
      >
        <header class="assistant-header" :class="{ 'assistant-header--page': isPageMode }">
          <div class="assistant-header-copy">
            <p class="assistant-kicker">{{ assistantHeading }}</p>
            <h3>{{ assistantTitle }}</h3>
            <p class="assistant-subtitle">{{ assistantSubtitle }}</p>
            <div v-if="isPageMode && currentUser" class="assistant-user-context">
              <strong>{{ currentUser.username }}</strong>
              <span>{{ roleText(currentUser.role) }} · 用户 ID {{ currentUser.id }}</span>
            </div>
          </div>
          <div class="assistant-header-actions">
            <button class="assistant-reset" type="button" @click="resetConversation">
              {{ resetButtonLabel }}
            </button>
            <button v-if="!isPageMode" class="assistant-close" type="button" @click="expanded = false">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </header>

        <div class="assistant-body">
          <div ref="messagesRef" class="assistant-messages">
            <article
              v-for="item in messages"
              :key="item.id"
              class="assistant-message"
              :class="item.role"
            >
              <div class="avatar">{{ item.role === 'user' ? 'U' : 'AI' }}</div>
              <div class="bubble">
                <!-- 如果解析到酒店推荐，渲染卡片网格 -->
                <HotelCardGrid
                  v-if="item.role === 'assistant' && item.hotelCards"
                  :categories="item.hotelCards"
                />
                <!-- 否则渲染普通文本 -->
                <p v-else>{{ item.content }}</p>

                <!-- 保留原有的推荐面板（用于其他类型推荐） -->
                <section
                  v-if="item.role === 'assistant' && item.recommendations?.cards?.length && !item.hotelCards"
                  class="recommendation-panel"
                >
                  <div class="recommendation-header">
                    <strong>{{ item.recommendations.title || '酒店推荐' }}</strong>
                    <span v-if="item.recommendations.count" class="recommendation-count">
                      {{ item.recommendations.count }} 家
                    </span>
                  </div>
                  <p v-if="item.recommendations.subtitle" class="recommendation-subtitle">
                    {{ item.recommendations.subtitle }}
                  </p>
                  <div class="recommendation-list">
                    <article
                      v-for="card in item.recommendations.cards"
                      :key="card.id || card.detailUrl || card.name"
                      class="recommendation-card"
                    >
                      <div class="recommendation-card-main">
                        <div class="recommendation-title-row">
                          <strong class="recommendation-title">{{ card.name || '酒店推荐' }}</strong>
                          <span v-if="card.rating" class="recommendation-rating">★ {{ card.rating }}</span>
                        </div>
                        <p v-if="card.location || card.address" class="recommendation-location">
                          {{ [card.location, card.address].filter(Boolean).join(' · ') }}
                        </p>
                        <p v-if="card.summary" class="recommendation-summary">{{ card.summary }}</p>
                        <div v-if="card.highlights?.length" class="recommendation-tags">
                          <span
                            v-for="tag in card.highlights.slice(0, 4)"
                            :key="`${card.id || card.name}-${tag}`"
                            class="recommendation-tag"
                          >
                            {{ tag }}
                          </span>
                        </div>
                        <!-- 房型信息 -->
                        <div v-if="card.roomTypes?.length" class="recommendation-rooms">
                          <p class="recommendation-rooms-title">可选房型</p>
                          <div class="recommendation-room-list">
                            <div
                              v-for="(room, idx) in card.roomTypes"
                              :key="`${card.id || card.name}-room-${idx}`"
                              class="recommendation-room-item"
                            >
                              <strong>{{ room.name }}</strong>
                              <span v-if="room.price" class="recommendation-room-price">{{ room.price }}</span>
                              <div class="recommendation-room-meta">
                                <span v-if="room.size">{{ room.size }}</span>
                                <span v-if="room.bedType">{{ room.bedType }}</span>
                                <span v-if="room.maxOccupancy">{{ room.maxOccupancy }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="recommendation-card-side">
                        <div v-if="card.priceLabel" class="recommendation-price">{{ card.priceLabel }}</div>
                        <div class="recommendation-actions">
                          <a
                            v-if="resolveDetailUrl(card)"
                            class="recommendation-link primary"
                            :href="resolveDetailUrl(card)"
                            target="_blank"
                            rel="noreferrer"
                          >
                            查看详情
                          </a>
                          <a
                            v-if="resolveBookingUrl(card)"
                            class="recommendation-link secondary"
                            :href="resolveBookingUrl(card)"
                            target="_blank"
                            rel="noreferrer"
                          >
                            立即预订
                          </a>
                        </div>
                      </div>
                    </article>
                  </div>
                </section>
                <span v-if="item.meta" class="meta">{{ item.meta }}</span>
              </div>
            </article>

            <article v-if="loading && streamingText" class="assistant-message assistant">
              <div class="avatar">AI</div>
              <div class="bubble">
                <p>{{ streamingText }}<span class="cursor-blink">|</span></p>
              </div>
            </article>
            <article v-else-if="loading && !streamingText" class="assistant-message assistant">
              <div class="avatar">AI</div>
              <div class="bubble typing">
                <span></span><span></span><span></span>
              </div>
            </article>
            <div v-if="toolCalls.length" class="tool-status-bar">
              <span
                v-for="t in toolCalls"
                :key="`${t.tool}-${t.status}`"
                class="tool-status-pill"
                :class="t.status"
              >
                <span class="tool-dot"></span>
                {{ t.label || t.tool }}
              </span>
            </div>
          </div>
        </div>

        <footer class="assistant-footer">
          <div v-if="suggestions.length" class="suggestion-chips">
            <button
              v-for="(s, idx) in suggestions"
              :key="idx"
              class="suggestion-chip"
              type="button"
              :disabled="loading"
              @click="quickSend(s)"
            >
              {{ s }}
            </button>
          </div>
          <div class="input-wrap">
            <textarea
              v-model="draft"
              rows="3"
              placeholder="例如：订单 BOOK20250401001 现在是什么状态？深圳南山有哪些评分高的民宿？"
              :disabled="loading"
              @keydown.enter.exact.prevent="submit"
            />
          </div>
          <div class="footer-row">
            <span class="status" :class="{ error: !!errorText }">
              {{ errorText || footerStatusText }}
            </span>
            <el-button type="primary" :loading="loading" @click="submit">发送</el-button>
          </div>
        </footer>
      </section>
    </transition>

    <button v-if="!isPageMode" class="assistant-trigger" type="button" @click="togglePanel" aria-label="打开 AI 助手">
      <span class="trigger-sparkle" aria-hidden="true">✦</span>
      <span class="trigger-badge">AI</span>
    </button>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ChatLineRound, Close } from '@element-plus/icons-vue'
import { assistantApi } from '../api'
import HotelCardGrid from './hotel/HotelCardGrid.vue'
import { parseHotelRecommendations } from '../utils/hotelParser'

const props = defineProps({
  mode: {
    type: String,
    default: 'floating'
  }
})

const isPageMode = computed(() => props.mode === 'page')
const expanded = ref(isPageMode.value)
const loading = ref(false)
const errorText = ref('')
const draft = ref('')
const conversationId = ref('')
const messagesRef = ref(null)
const streamingText = ref('')
const toolCalls = ref([])
const suggestions = ref([])
const currentUser = ref(null)

const assistantHeading = computed(() => (isPageMode.value ? 'AI Copilot Workspace' : 'LLM Customer Agent'))
const assistantTitle = computed(() => (isPageMode.value ? 'AI 客服工作台' : '客服助手'))
const assistantSubtitle = computed(() => {
  if (!isPageMode.value) {
    return '面向订单、支付、房源、评价、通知和优惠券的智能客服入口。'
  }
  return '已接入主站登录身份，AI 会优先结合你的账号上下文处理订单、支付、通知和房源问题。'
})
const resetButtonLabel = computed(() => (isPageMode.value ? '清空会话' : '新建对话'))
const footerStatusText = computed(() => {
  if (!isPageMode.value) {
    return '当前由 Flask 微服务 + LLM + 后端技能工具提供客服能力。'
  }
  return '当前会话会自动透传登录 token，并将你的身份信息带入 AI 客服服务。'
})

const buildWelcomeMessage = () => ({
  id: 'welcome',
  role: 'assistant',
  content: '我是你的 AI 客服助手，可以帮你查询订单、支付、房源、评价、通知和优惠券信息。你可以试试下面的快捷提问。',
  meta: 'Flask + LLM + Backend Skills',
  recommendations: null
})

const messages = ref([buildWelcomeMessage()])

const PROPERTY_DETAIL_BASE_URL = 'http://localhost:5400'
const PROPERTY_DETAIL_PATH_RE = /^\/property\/[^?#]+(?:[?#].*)?$/i
const LOCALHOST_PROPERTY_URL_RE = /^https?:\/\/localhost(?::\d+)?(\/property\/[^?#]+(?:[?#].*)?)$/i

const normalizeUrl = (url) => {
  if (!url || typeof url !== 'string') return ''
  const trimmed = url.trim()
  if (!trimmed) return ''
  const localhostPropertyMatch = trimmed.match(LOCALHOST_PROPERTY_URL_RE)
  if (localhostPropertyMatch) {
    return `${PROPERTY_DETAIL_BASE_URL}${localhostPropertyMatch[1]}`
  }
  if (PROPERTY_DETAIL_PATH_RE.test(trimmed)) {
    return `${PROPERTY_DETAIL_BASE_URL}${trimmed}`
  }
  if (/^https?:\/\//i.test(trimmed) || trimmed.startsWith('/')) return trimmed
  return ''
}

const resolveDetailUrl = (card) => normalizeUrl(card?.detailUrl)
const resolveBookingUrl = (card) => normalizeUrl(card?.bookingUrl)

const scrollToBottom = async () => {
  if (!expanded.value && !isPageMode.value) return
  await nextTick()
  const container = messagesRef.value
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

const togglePanel = () => {
  expanded.value = !expanded.value
  if (expanded.value && suggestions.value.length === 0) {
    loadSuggestions()
  }
}

watch(() => messages.value.length, scrollToBottom)
watch(loading, scrollToBottom)
watch(streamingText, scrollToBottom)
watch(expanded, (value) => {
  if (value) scrollToBottom()
})
watch(isPageMode, (value) => {
  if (value) expanded.value = true
})

const resetConversation = () => {
  conversationId.value = ''
  errorText.value = ''
  draft.value = ''
  streamingText.value = ''
  toolCalls.value = []
  messages.value = [buildWelcomeMessage()]
}

const loadSuggestions = async () => {
  try {
    const { data } = await assistantApi.getSuggestions()
    suggestions.value = Array.isArray(data) ? data : []
  } catch (error) {
    suggestions.value = []
  }
}

const quickSend = (text) => {
  draft.value = text
  submit()
}

const getStoredUser = () => {
  try {
    const rawUser = localStorage.getItem('user')
    if (!rawUser) return null
    return JSON.parse(rawUser)
  } catch (error) {
    return null
  }
}

const syncCurrentUser = () => {
  currentUser.value = getStoredUser()
}

const resolveUserContext = () => {
  const user = getStoredUser()
  if (!user) return null
  return {
    id: user.id,
    username: user.username,
    role: user.role,
    merchantId: user.merchantId ?? null
  }
}

const resolveAuthHeaders = () => {
  const user = getStoredUser()
  if (!user?.token) return {}
  return {
    Authorization: `Bearer ${user.token}`
  }
}

const roleText = (role) => {
  const roleMap = {
    USER: '普通用户',
    MERCHANT: '商户',
    ADMIN: '管理员'
  }
  return roleMap[role] || role || '访客'
}

const submit = async () => {
  const message = draft.value.trim()
  if (!message || loading.value) return

  errorText.value = ''
  streamingText.value = ''
  toolCalls.value = []

  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: message,
    recommendations: null
  })
  draft.value = ''
  loading.value = true

  try {
    const currentUserContext = resolveUserContext()
    const response = await fetch('/ai-api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...resolveAuthHeaders()
      },
      body: JSON.stringify({
        message,
        conversationId: conversationId.value,
        userContext: currentUserContext
      })
    })

    if (!response.ok || !response.body) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let finalAnswer = ''
    let finalSource = ''
    let finalRecommendations = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue

        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'chunk') {
            streamingText.value += event.content || ''
          } else if (event.type === 'meta') {
            conversationId.value = event.conversationId || conversationId.value
          } else if (event.type === 'tool_start') {
            toolCalls.value = [...toolCalls.value, { ...event, status: 'running' }]
          } else if (event.type === 'tool_end') {
            toolCalls.value = toolCalls.value.map((tool) =>
              tool.tool === event.tool ? { ...tool, ...event, status: event.status } : tool
            )
          } else if (event.type === 'done') {
            finalAnswer = event.answer || streamingText.value
            finalSource = event.source || ''
            finalRecommendations = event.recommendations || null
          } else if (event.type === 'error') {
            throw new Error(event.error || 'Stream error')
          }
        } catch (error) {
          if (error.message === 'Stream error') {
            throw error
          }
        }
      }
    }

    if (!finalAnswer && streamingText.value) {
      finalAnswer = streamingText.value
    }

    // 尝试解析酒店推荐
    const hotelCards = parseHotelRecommendations(finalAnswer)

    messages.value.push({
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: finalAnswer || 'AI 没有返回内容。',
      meta: finalSource || 'streaming',
      recommendations: finalRecommendations,
      hotelCards: hotelCards
    })
    streamingText.value = ''
    toolCalls.value = []
  } catch (error) {
    console.error('AI stream error:', error)

    try {
      const currentUserContext = resolveUserContext()
      const { data } = await assistantApi.chat({
        message,
        conversationId: conversationId.value,
        userContext: currentUserContext
      })

      conversationId.value = data.conversationId || conversationId.value

      // 尝试解析酒店推荐
      const hotelCards = parseHotelRecommendations(data.answer)

      messages.value.push({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer || '服务已返回，但没有生成回答。',
        meta: data.source || 'fallback',
        recommendations: data.recommendations || null,
        hotelCards: hotelCards
      })
    } catch (fallbackError) {
      errorText.value = 'AI 服务暂时不可用，请检查 Flask 服务和后端接口。'
      messages.value.push({
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: '这次没有成功拿到结果。请先确认 Flask AI 服务和后端服务都已经启动。',
        meta: 'error',
        recommendations: null
      })
    }
    streamingText.value = ''
    toolCalls.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  syncCurrentUser()
  loadSuggestions()
  window.addEventListener('user-changed', syncCurrentUser)
  window.addEventListener('storage', syncCurrentUser)
})

onBeforeUnmount(() => {
  window.removeEventListener('user-changed', syncCurrentUser)
  window.removeEventListener('storage', syncCurrentUser)
})
</script>

<style scoped>
.assistant-shell {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 40;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}

.assistant-shell--page {
  position: relative;
  right: auto;
  bottom: auto;
  width: 100%;
  align-items: stretch;
  gap: 0;
}

.assistant-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 76px;
  height: 76px;
  border: none;
  cursor: pointer;
  padding: 0;
  border-radius: 24px;
  background: linear-gradient(135deg, #d79a7a 0%, #e7a186 38%, #f3b1a7 72%, #f7c7c0 100%);
  color: #fffaf7;
  box-shadow: 0 22px 42px rgba(198, 123, 96, 0.28);
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.assistant-trigger::before {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: 23px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
}

.assistant-trigger:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 28px 50px rgba(198, 123, 96, 0.34);
}

.trigger-badge {
  position: relative;
  z-index: 1;
  width: 48px;
  height: 48px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0.04em;
  background: rgba(255, 250, 247, 0.2);
  border: 1px solid rgba(255, 250, 247, 0.26);
  backdrop-filter: blur(8px);
}

.trigger-sparkle {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 1;
  font-size: 13px;
  color: rgba(255, 250, 247, 0.96);
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.6);
  animation: sparkle-glow 1.8s ease-in-out infinite;
}

@keyframes sparkle-glow {
  0%,
  100% {
    opacity: 0.72;
    transform: scale(0.92) rotate(0deg);
  }

  50% {
    opacity: 1;
    transform: scale(1.12) rotate(12deg);
  }
}

.assistant-panel {
  width: min(420px, calc(100vw - 24px));
  height: clamp(520px, 68vh, 680px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(66, 153, 225, 0.16), transparent 28%),
    linear-gradient(180deg, rgba(247, 251, 255, 0.98), rgba(236, 246, 255, 0.98));
  border: 1px solid rgba(92, 153, 255, 0.18);
  box-shadow: 0 28px 70px rgba(14, 62, 121, 0.22);
  backdrop-filter: blur(14px);
}

.assistant-panel--page {
  width: 100%;
  height: min(80vh, 860px);
  min-height: 720px;
  border-radius: 32px;
  background:
    radial-gradient(circle at top left, rgba(66, 153, 225, 0.18), transparent 26%),
    linear-gradient(180deg, rgba(237, 246, 255, 0.98), rgba(228, 239, 250, 0.98));
}

.assistant-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px 14px;
  background: linear-gradient(135deg, rgba(10, 76, 160, 0.95), rgba(30, 149, 221, 0.92));
  color: #fff;
}

.assistant-header--page {
  padding: 24px 24px 18px;
}

.assistant-header-copy {
  min-width: 0;
}

.assistant-kicker {
  margin: 0 0 6px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(220, 241, 255, 0.78);
}

.assistant-header h3 {
  margin: 0;
  font-size: 22px;
}

.assistant-header--page h3 {
  font-size: 28px;
}

.assistant-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: rgba(227, 244, 255, 0.88);
}

.assistant-header--page .assistant-subtitle {
  max-width: 720px;
  font-size: 14px;
}

.assistant-user-context {
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #ffffff;
}

.assistant-user-context strong {
  font-size: 14px;
  font-weight: 700;
}

.assistant-user-context span {
  font-size: 12px;
  color: rgba(231, 245, 255, 0.82);
}

.assistant-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.assistant-reset,
.assistant-close {
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
}

.assistant-reset {
  min-height: 36px;
  padding: 0 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}

.assistant-close {
  width: 36px;
  height: 36px;
  border-radius: 12px;
}

.assistant-body {
  min-height: 0;
  padding: 16px 18px 10px;
}

.assistant-panel--page .assistant-body {
  padding: 20px 22px 12px;
}

.assistant-messages {
  height: 100%;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 4px;
}

.assistant-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.assistant-message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #1274ea, #24b0db);
  flex-shrink: 0;
}

.user .avatar {
  background: linear-gradient(135deg, #0f172a, #334155);
}

.bubble {
  max-width: 78%;
  max-height: min(360px, 45vh);
  overflow-y: auto;
  padding: 14px 15px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(56, 135, 255, 0.12);
  box-shadow: 0 12px 24px rgba(16, 66, 133, 0.08);
  scrollbar-gutter: stable;
}

.assistant-panel--page .bubble {
  max-width: 72%;
}

.user .bubble {
  background: linear-gradient(135deg, #1466d9, #1da6de);
  color: #fff;
}

.bubble p {
  margin: 0;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.recommendation-panel {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(56, 135, 255, 0.12);
}

.recommendation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.recommendation-count {
  font-size: 12px;
  color: #4b698b;
}

.recommendation-subtitle {
  margin: 8px 0 0;
  font-size: 12px;
  color: #4b698b;
}

.recommendation-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recommendation-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(56, 135, 255, 0.12);
  background: rgba(247, 251, 255, 0.96);
}

.recommendation-card-main {
  min-width: 0;
}

.recommendation-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.recommendation-title {
  font-size: 14px;
  line-height: 1.5;
  color: #0f172a;
}

.recommendation-rating {
  flex-shrink: 0;
  font-size: 12px;
  color: #d97706;
}

.recommendation-location,
.recommendation-summary {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: #4b698b;
}

.recommendation-tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.recommendation-tag {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 11px;
}

.recommendation-rooms {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(56, 135, 255, 0.12);
}

.recommendation-rooms-title {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 600;
  color: #4b698b;
}

.recommendation-room-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recommendation-room-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.04);
  border: 1px solid rgba(56, 135, 255, 0.12);
}

.recommendation-room-item strong {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.recommendation-room-price {
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
}

.recommendation-room-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 11px;
  color: #4b698b;
}

.recommendation-room-meta span {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(37, 99, 235, 0.06);
}

.recommendation-card-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
}

.recommendation-price {
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
  text-align: right;
}

.recommendation-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: stretch;
}

.recommendation-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  padding: 8px 12px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 12px;
  line-height: 1;
}

.recommendation-link.primary {
  background: linear-gradient(135deg, #1466d9, #1da6de);
  color: #fff;
}

.recommendation-link.secondary {
  border: 1px solid rgba(20, 102, 217, 0.22);
  color: #1466d9;
  background: #fff;
}

.meta {
  display: inline-block;
  margin-top: 8px;
  font-size: 11px;
  color: rgba(78, 101, 132, 0.75);
}

.user .meta {
  color: rgba(255, 255, 255, 0.74);
}

.typing {
  display: flex;
  align-items: center;
  gap: 6px;
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5fa8ff;
  animation: pulse 1s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.18s;
}

.typing span:nth-child(3) {
  animation-delay: 0.36s;
}

.assistant-footer {
  padding: 14px 18px 18px;
  background: rgba(255, 255, 255, 0.82);
  border-top: 1px solid rgba(84, 145, 246, 0.12);
}

.assistant-panel--page .assistant-footer {
  padding: 16px 22px 22px;
}

.input-wrap {
  border-radius: 18px;
  background: #fff;
  border: 1px solid rgba(69, 132, 240, 0.14);
}

.input-wrap textarea {
  width: 100%;
  resize: none;
  border: none;
  background: transparent;
  padding: 14px 14px 10px;
  outline: none;
  color: #0f172a;
  font: inherit;
  min-height: 86px;
}

.footer-row {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.status {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #4b698b;
}

.status.error {
  color: #c2410c;
}

.assistant-panel-enter-active,
.assistant-panel-leave-active {
  transition: all 0.24s ease;
}

.assistant-panel-enter-from,
.assistant-panel-leave-to {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}

.cursor-blink {
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  50% {
    opacity: 0;
  }
}

.suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  padding: 0 2px;
}

.suggestion-chip {
  border: 1px solid rgba(56, 135, 255, 0.18);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12px;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.06);
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-chip:hover {
  background: rgba(37, 99, 235, 0.14);
  border-color: rgba(37, 99, 235, 0.32);
}

.suggestion-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-status-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 10px;
}

.tool-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  color: #4b698b;
  background: rgba(56, 135, 255, 0.06);
  border: 1px solid rgba(56, 135, 255, 0.1);
}

.tool-status-pill.running {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
}

.tool-status-pill.ok {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
}

.tool-status-pill.error {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.06);
}

.tool-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.tool-status-pill.running .tool-dot {
  animation: pulse 1s infinite ease-in-out;
}

@keyframes pulse {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .assistant-shell {
    right: 12px;
    left: 12px;
    bottom: 12px;
  }

  .assistant-shell--page {
    left: auto;
    bottom: auto;
  }

  .assistant-trigger,
  .assistant-panel {
    width: 100%;
  }

  .assistant-trigger {
    width: 72px;
    height: 72px;
  }

  .assistant-panel {
    height: clamp(440px, 72vh, 620px);
  }

  .assistant-panel--page {
    min-height: 0;
    height: calc(100vh - 190px);
    border-radius: 24px;
  }

  .bubble,
  .assistant-panel--page .bubble {
    max-width: 84%;
    max-height: min(320px, 42vh);
  }

  .recommendation-card {
    grid-template-columns: 1fr;
  }

  .recommendation-card-side {
    align-items: stretch;
  }

  .recommendation-price {
    text-align: left;
  }

  .footer-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
