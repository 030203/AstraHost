import { assistantApi } from './index'
import { getStoredUser } from '../composables/useSession'

export const readAssistantUserContext = () => {
  const user = getStoredUser()
  if (!user?.id || !user?.username) {
    return null
  }

  const roleValue = String(user.role || 'USER').trim().toUpperCase()
  const role = ['USER', 'MERCHANT', 'ADMIN'].includes(roleValue) ? roleValue : 'USER'

  return {
    id: String(user.id),
    username: String(user.username),
    role,
    merchantId:
      user.merchantId === '' || user.merchantId === null || user.merchantId === undefined
        ? null
        : String(user.merchantId),
    avatar: user.avatar || ''
  }
}

export const getAssistantSuggestions = async () => {
  const { data } = await assistantApi.getSuggestions()
  return Array.isArray(data) ? data : []
}

export const getAssistantConversationIds = async () => {
  const { data } = await assistantApi.getConversations()
  return Array.isArray(data?.conversationIds) ? data.conversationIds : []
}

export const getAssistantConversationMessages = async (conversationId) => {
  const { data } = await assistantApi.getConversationMessages(conversationId)
  return Array.isArray(data?.messages) ? data.messages : []
}

export const streamAssistantChat = async ({
  message,
  conversationId,
  userContext,
  pendingAction,
  signal,
  onEvent
}) => {
  const user = getStoredUser()
  const headers = {
    'Content-Type': 'application/json'
  }

  if (user?.token) {
    headers.Authorization = `Bearer ${user.token}`
  }

  const response = await fetch('/ai-api/chat/stream', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      conversationId,
      userContext,
      pendingAction: pendingAction || null
    }),
    signal
  })

  if (!response.ok || !response.body) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  const emitChunk = (chunk) => {
    const line = chunk
      .split('\n')
      .find((item) => item.startsWith('data: '))

    if (!line) return
    onEvent(JSON.parse(line.slice(6)))
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      buffer += decoder.decode()
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''

    for (const chunk of chunks) {
      emitChunk(chunk)
    }
  }

  const tail = buffer.trim()
  if (tail) emitChunk(tail)
}
