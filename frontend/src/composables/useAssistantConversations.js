import { computed, ref } from 'vue'

const STORAGE_KEY = 'ai-service-copilot-conversations'
const MAX_CONVERSATIONS = 50

const normalizeMessage = (message, index = 0) => {
  if (!message || typeof message !== 'object') return null

  const role = String(message.role || '').trim()
  if (!role) return null

  const content =
    typeof message.content === 'string'
      ? message.content
      : message.content == null
        ? ''
        : String(message.content)

  return {
    id: message.id || `message-${Date.now()}-${index}-${Math.random().toString(16).slice(2, 8)}`,
    role,
    content,
    createdAt:
      typeof message.createdAt === 'number' && Number.isFinite(message.createdAt)
        ? message.createdAt
        : Date.now(),
    error: Boolean(message.error),
    recommendations: message.recommendations || null,
    pendingAction: message.pendingAction || null
  }
}

const normalizeEntry = (entry) => {
  if (!entry || typeof entry !== 'object') return null

  const id = String(entry.id || '').trim()
  if (!id) return null

  const messages = Array.isArray(entry.messages)
    ? entry.messages
        .map((message, index) => normalizeMessage(message, index))
        .filter(Boolean)
    : []

  return {
    id,
    title: String(entry.title || '历史会话'),
    updatedAt:
      typeof entry.updatedAt === 'number' && Number.isFinite(entry.updatedAt)
        ? entry.updatedAt
        : Date.now(),
    messages
  }
}

const readStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    if (!Array.isArray(parsed)) return []
    return parsed.map(normalizeEntry).filter(Boolean)
  } catch (error) {
    return []
  }
}

export const useAssistantConversations = () => {
  const items = ref(readStorage())

  const persist = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value.slice(0, MAX_CONVERSATIONS)))
  }

  const save = (entry) => {
    if (!entry || !entry.id) return

    const existing = items.value.find((item) => item.id === entry.id)
    const merged = existing ? { ...existing, ...entry } : entry
    const normalized = normalizeEntry(merged)
    if (!normalized) return

    const next = items.value.filter((item) => item.id !== normalized.id)
    items.value = [normalized, ...next].slice(0, MAX_CONVERSATIONS)
    persist()
  }

  const remove = (id) => {
    items.value = items.value.filter((item) => item.id !== id)
    persist()
  }

  const syncRemote = (ids) => {
    if (!Array.isArray(ids) || !ids.length) return

    const map = new Map(items.value.map((item) => [item.id, item]))
    ids.forEach((id) => {
      if (!map.has(id)) {
        map.set(id, {
          id,
          title: '历史会话',
          updatedAt: Date.now(),
          messages: []
        })
      }
    })

    items.value = Array.from(map.values())
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, MAX_CONVERSATIONS)
    persist()
  }

  const getById = (id) => items.value.find((item) => item.id === id) || null

  return {
    items: computed(() => items.value),
    save,
    remove,
    syncRemote,
    getById
  }
}
